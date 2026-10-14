"""Authentication, session context, organizational hierarchy, and user/group management endpoints."""

from typing import List, Optional
import hmac
import os

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from src.cadence_tprm.database import get_db
from src.cadence_tprm.config import settings
from src.cadence_tprm.models.identity import Organization, Department, UserGroup, User, GroupMembership, Role, Permission
from src.cadence_tprm.services.auth_service import AuthService, create_access_token, get_current_user, require_tprm_admin
from src.cadence_tprm.services.audit_service import AuditService

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)

class CreateGroupRequest(BaseModel):
    name: str
    description: str
    default_permission: str = "Edit"
    department_code: Optional[str] = None
    user_emails: List[str] = []

class AddGroupMemberRequest(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role_in_group: str = "Edit"  # Admin or Edit

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    configured_password = os.getenv("TPRM_DEMO_PASSWORD") or settings.DEMO_LOGIN_PASSWORD
    if not configured_password or not hmac.compare_digest(req.password, configured_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    profile = AuthService.get_user_profile(db, req.email.lower().strip())
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found in TPRM user directory or inactive."
        )

    token = create_access_token({"sub": profile["email"]})
    AuditService.log_event(
        db,
        actor_email=profile["email"],
        action="USER_LOGIN",
        entity_type="USER",
        entity_id=profile["id"],
        details={"groups": profile["groups"], "is_admin": profile["is_admin"]}
    )
    return {
        "user": profile,
        "access_token": token,
        "token_type": "bearer"
    }

@router.get("/me")
def get_current_session(
    email: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    if email:
        target = AuthService.get_user_profile(db, email.lower().strip())
        if not target:
            raise HTTPException(status_code=404, detail=f"User '{email}' not found.")
        return {**target, "user": target}
    return {**user, "user": user}

@router.get("/users")
def list_users(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Lists all directory users and their assigned TPRM groups and roles."""
    users = db.query(User).all()
    output = []
    for u in users:
        p = AuthService.get_user_profile(db, u.email, include_inactive=True)
        if p:
            output.append(p)
    return {"users": output, "items": output}

@router.get("/hierarchy")
def get_organization_hierarchy(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Returns the full Organization -> Departments -> Groups -> Users -> Roles -> Permissions hierarchy."""
    org = db.query(Organization).first()
    depts = db.query(Department).all()
    groups = db.query(UserGroup).all()
    roles = db.query(Role).all()
    perms = db.query(Permission).all()
    users = db.query(User).all()

    groups_out = []
    for g in groups:
        memberships = db.query(GroupMembership).filter_by(group_id=g.id).all()
        members = []
        for m in memberships:
            u = db.query(User).filter_by(id=m.user_id).first()
            if u:
                members.append({
                    "id": u.id,
                    "email": u.email,
                    "full_name": u.full_name,
                    "is_active": u.is_active,
                    "role_in_group": m.role_in_group,
                    "role_code": m.role_code,
                })
        groups_out.append({
            "id": g.id,
            "name": g.name,
            "description": g.description,
            "default_permission": g.default_permission,
            "review_sections": g.review_sections or [],
            "members_count": len(members),
            "members": members,
        })

    return {
        "organization": {
            "id": org.id if org else "org-1",
            "name": org.name if org else "Cadence Design Systems",
            "domain": org.domain if org else "cadence.com",
        },
        "departments": [
            {"id": d.id, "name": d.name, "code": d.code, "description": d.description}
            for d in depts
        ],
        "groups": groups_out,
        "roles": [
            {"id": r.id, "code": r.code, "name": r.name, "description": r.description, "permissions": r.permissions}
            for r in roles
        ],
        "permissions": [
            {"code": p.code, "resource": p.resource, "action": p.action, "description": p.description}
            for p in perms
        ],
        "total_users": len(users),
    }

@router.post("/groups", status_code=status.HTTP_201_CREATED)
def create_user_group(
    req: CreateGroupRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_tprm_admin)
):
    """Implements Section 6.1: Create User Group, add users, and assign roles."""
    if db.query(UserGroup).filter_by(name=req.name.strip()).first():
        raise HTTPException(status_code=400, detail=f"User group '{req.name}' already exists.")

    dept = db.query(Department).filter_by(code=req.department_code).first() if req.department_code else None
    group = UserGroup(
        department_id=dept.id if dept else None,
        name=req.name.strip(),
        description=req.description,
        default_permission=req.default_permission,
        review_sections=["Custom Assigned Sections"],
    )
    db.add(group)
    db.flush()

    for em in req.user_emails:
        u = db.query(User).filter_by(email=em.strip().lower()).first()
        if u:
            db.add(GroupMembership(
                user_id=u.id,
                group_id=group.id,
                role_in_group=req.default_permission,
                role_code="TPRM_ADMIN" if req.default_permission == "Admin" else "DEPT_REVIEWER",
            ))

    AuditService.log_event(
        db,
        actor_email=current_user["email"],
        action="USER_GROUP_CREATED",
        entity_type="USER_GROUP",
        entity_id=group.id,
        details={"name": group.name, "default_permission": group.default_permission, "members": req.user_emails}
    )
    db.commit()
    return {"status": "created", "group_id": group.id, "name": group.name}

@router.post("/groups/{group_id}/members")
def add_member_to_group(
    group_id: str,
    req: AddGroupMemberRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_tprm_admin)
):
    group = db.query(UserGroup).filter_by(id=group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="User group not found.")

    email_norm = req.email.strip().lower()
    user = db.query(User).filter_by(email=email_norm).first()
    if not user:
        org = db.query(Organization).first()
        user = User(
            organization_id=org.id if org else None,
            email=email_norm,
            full_name=req.full_name or email_norm.split("@")[0].replace(".", " ").title() + " (Synthetic Demo)",
            title="TPRM Specialist",
            is_tprm_admin=(req.role_in_group == "Admin" and group.name == "Vendor Risk Management Group"),
            is_active=True,
            is_synthetic=True,
        )
        db.add(user)
        db.flush()

    existing = db.query(GroupMembership).filter_by(user_id=user.id, group_id=group.id).first()
    if existing:
        existing.role_in_group = req.role_in_group
        existing.role_code = "TPRM_ADMIN" if req.role_in_group == "Admin" else "DEPT_REVIEWER"
    else:
        db.add(GroupMembership(
            user_id=user.id,
            group_id=group.id,
            role_in_group=req.role_in_group,
            role_code="TPRM_ADMIN" if req.role_in_group == "Admin" else "DEPT_REVIEWER",
        ))

    if group.name == "Vendor Risk Management Group" and req.role_in_group == "Admin":
        user.is_tprm_admin = True

    AuditService.log_event(
        db,
        actor_email=current_user["email"],
        action="GROUP_MEMBER_ADDED",
        entity_type="USER_GROUP",
        entity_id=group.id,
        details={"user_email": user.email, "group": group.name, "role_in_group": req.role_in_group}
    )
    db.commit()
    return {"status": "member_added", "user_email": user.email, "group_name": group.name}

@router.post("/users/{user_id}/toggle-active")
def toggle_user_active(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_tprm_admin)
):
    """Implements Section 6.1 & 7.10 annual membership review user activation/deactivation."""
    u = db.query(User).filter_by(id=user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found.")
    if u.email == current_user["email"]:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own active administrator session.")

    u.is_active = not u.is_active
    AuditService.log_event(
        db,
        actor_email=current_user["email"],
        action="USER_STATUS_TOGGLED",
        entity_type="USER",
        entity_id=u.id,
        details={"email": u.email, "is_active": u.is_active}
    )
    db.commit()
    return {"status": "updated", "user_id": u.id, "is_active": u.is_active}
