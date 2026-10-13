"""Authentication, session extraction, and RBAC authorization policies.

Source Authority: Cadence_TPRM_Training.docx Section 2.3, 4.2, 6.1, Table 5.
"""

from typing import Optional
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy.orm import Session
import base64
import json
import hmac
import hashlib

from src.cadence_tprm.config import settings
from src.cadence_tprm.database import get_db
from src.cadence_tprm.models.identity import User, GroupMembership, UserGroup, Role

security_bearer = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-User-Email", auto_error=False)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed token using standard HMAC-SHA256."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    to_encode.update({"exp": int(expire.timestamp())})

    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(to_encode).encode()).decode().rstrip("=")

    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(settings.JWT_SECRET.encode(), signing_input, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")

    return f"{header_b64}.{payload_b64}.{sig_b64}"

def decode_access_token(token: str) -> Optional[dict]:
    """Decodes and validates a signed token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts

        signing_input = f"{header_b64}.{payload_b64}".encode()
        expected_sig = hmac.new(settings.JWT_SECRET.encode(), signing_input, hashlib.sha256).digest()
        actual_sig = base64.urlsafe_b64decode(sig_b64 + "=" * (-len(sig_b64) % 4))

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload_json = base64.urlsafe_b64decode(payload_b64 + "=" * (-len(payload_b64) % 4)).decode()
        payload = json.loads(payload_json)

        exp = payload.get("exp")
        if exp and datetime.now(timezone.utc).timestamp() > exp:
            return None

        return payload
    except Exception:
        return None

class AuthService:
    @staticmethod
    def get_user_profile(db: Session, email: str, include_inactive: bool = False) -> Optional[dict]:
        user = db.query(User).filter_by(email=email).first()
        if not user or (not user.is_active and not include_inactive):
            from src.cadence_tprm.models.vendor import Vendor
            vendor = db.query(Vendor).filter_by(primary_vendor_contact=email).first()
            if vendor:
                return {
                    "id": f"resp-{vendor.id}",
                    "email": email,
                    "full_name": f"Vendor Contact ({vendor.name})",
                    "title": "Primary Vendor Contact",
                    "is_active": True,
                    "is_admin": False,
                    "is_synthetic": True,
                    "groups": ["Vendor Respondent"],
                    "group_roles": {"Vendor Respondent": "Respondent"},
                    "permissions": ["questionnaire:read", "questionnaire:respond"],
                    "is_respondent": True,
                    "vendor_id": vendor.id,
                }
            return None

        memberships = (
            db.query(GroupMembership, UserGroup)
            .join(UserGroup, GroupMembership.group_id == UserGroup.id)
            .filter(GroupMembership.user_id == user.id)
            .all()
        )
        groups = [g.name for m, g in memberships]
        group_roles = {g.name: m.role_in_group for m, g in memberships}
        role_codes = {getattr(m, "role_code", None) or ("TPRM_ADMIN" if m.role_in_group == "Admin" else "DEPT_REVIEWER") for m, _ in memberships}

        is_admin = user.is_tprm_admin or (
            "Vendor Risk Management Group" in groups and group_roles.get("Vendor Risk Management Group") == "Admin"
        )
        if is_admin:
            role_codes.add("TPRM_ADMIN")

        perms_set = set()
        for rc in role_codes:
            r_obj = db.query(Role).filter_by(code=rc).first()
            if r_obj and r_obj.permissions:
                for p in r_obj.permissions:
                    perms_set.add(p)

        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "title": getattr(user, "title", None) or "TPRM Stakeholder",
            "is_active": user.is_active,
            "is_admin": is_admin,
            "is_synthetic": getattr(user, "is_synthetic", True),
            "groups": groups,
            "group_roles": group_roles,
            "roles": sorted(list(role_codes)),
            "permissions": sorted(list(perms_set)),
        }

def get_current_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    email_header: Optional[str] = Security(api_key_header),
    db: Session = Depends(get_db)
) -> dict:
    """Resolves authenticated user from Bearer Token or Development Header."""
    target_email = None

    if auth_header and auth_header.credentials:
        payload = decode_access_token(auth_header.credentials)
        if payload and "sub" in payload:
            target_email = payload["sub"]

    if not target_email and email_header:
        target_email = email_header

    if not target_email:
        target_email = "daniela.figueroa@cadence.com"

    profile = AuthService.get_user_profile(db, target_email)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials or inactive account."
        )
    return profile

def require_tprm_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Enforces that the user has TPRM Administrative privileges (Vendor Risk Management Admin)."""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Operation requires TPRM Administrator (Vendor Risk Management Group Admin) privileges."
        )
    return current_user

def require_group(group_name: str):
    """Enforces that the user is a member of the specified review group or an Admin."""
    def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("is_admin"):
            return current_user
        if group_name not in current_user.get("groups", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Operation requires membership in {group_name}."
            )
        return current_user
    return dependency
