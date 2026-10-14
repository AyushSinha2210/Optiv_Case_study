"""Vendor management, Attribute Manager, Renewals, and Lifecycle endpoints."""

from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from src.cadence_tprm.database import get_db
from src.cadence_tprm.models.vendor import Vendor, VendorAttributeDefinition, RenewalDecision
from src.cadence_tprm.models.assessment import RiskFinding
from src.cadence_tprm.services.vendor_service import VendorService
from src.cadence_tprm.services.workflow_engine import WorkflowEngine
from src.cadence_tprm.services.audit_service import AuditService
from src.cadence_tprm.services.auth_service import get_current_user, require_tprm_admin

router = APIRouter(prefix="/vendors", tags=["Vendors"])

class VendorCreateRequest(BaseModel):
    name: str
    type: str = "Technology"
    criticality: str = "Medium"
    primary_vendor_contact: EmailStr
    business_owner: EmailStr
    vendor_tier: str
    vendor_category: str
    website: Optional[str] = ""

class VendorUpdateRequest(BaseModel):
    type: Optional[str] = None
    criticality: Optional[str] = None
    primary_vendor_contact: Optional[EmailStr] = None
    business_owner: Optional[EmailStr] = None
    vendor_tier: Optional[str] = None
    vendor_category: Optional[str] = None
    website: Optional[str] = None

class OffboardRequest(BaseModel):
    reason: str

class RenewalDecisionRequest(BaseModel):
    decision: str  # Renewed, Conditional Renewal, Non-Renewal / Offboard
    rationale: str

class AttributeCreateRequest(BaseModel):
    key_name: str
    description_key: str
    response_type: str = "Single select"
    options: List[str] = []

class AttributeUpdateRequest(BaseModel):
    description_key: Optional[str] = None
    add_option: Optional[str] = None
    is_active: Optional[bool] = None

@router.get("")
def list_vendors(
    category: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
    lifecycle_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return VendorService.list_vendors(
        db,
        category=category,
        tier=tier,
        lifecycle_status=lifecycle_status,
        search=search,
        page=page,
        page_size=page_size
    )

@router.post("", status_code=status.HTTP_201_CREATED)
def create_vendor(
    req: VendorCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    req_data = getattr(req, "model_dump", req.dict)()
    vendor = VendorService.create_vendor(db, req_data, actor_email=current_user["email"])
    return {
        "status": "created",
        "vendor_id": vendor.id,
        "name": vendor.name,
        "workflow": vendor.current_workflow_name,
        "stage": vendor.current_stage,
        "lifecycle_status": vendor.lifecycle_status
    }

@router.get("/attributes/inventory")
def list_attribute_definitions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    attrs = db.query(VendorAttributeDefinition).order_by(VendorAttributeDefinition.key_name.asc()).all()
    items = [
        {
            "id": a.id,
            "key_name": a.key_name,
            "display_name": a.display_name,
            "description_key": a.description_key,
            "response_type": a.response_type,
            "options": a.options or [],
            "source": a.source,
            "direction": a.direction,
            "is_mandatory": a.is_mandatory,
            "is_active": a.is_active,
            "is_workflow_driver": a.is_workflow_driver,
            "last_reviewed_at": a.last_reviewed_at.isoformat() if a.last_reviewed_at else None,
        }
        for a in attrs
    ]
    return {"items": items, "attributes": items}

@router.post("/attributes/inventory", status_code=status.HTTP_201_CREATED)
def create_attribute_definition(
    req: AttributeCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_tprm_admin)
):
    if db.query(VendorAttributeDefinition).filter_by(key_name=req.key_name.strip()).first():
        raise HTTPException(status_code=400, detail=f"Attribute '{req.key_name}' already exists.")
    attr = VendorAttributeDefinition(
        key_name=req.key_name.strip(),
        display_name=req.key_name.strip(),
        description_key=req.description_key,
        response_type=req.response_type,
        options=req.options,
        source="Custom",
        direction="From: Ironclad To: OneTrust",
        is_mandatory=False,
        is_active=True,
        is_workflow_driver=False,
    )
    db.add(attr)
    AuditService.log_event(
        db,
        actor_email=current_user["email"],
        action="ATTRIBUTE_CREATED",
        entity_type="ATTRIBUTE",
        entity_id=attr.id,
        details={"key_name": attr.key_name, "response_type": attr.response_type, "options": attr.options}
    )
    db.commit()
    return {"status": "created", "id": attr.id, "key_name": attr.key_name}

@router.put("/attributes/inventory/{attr_id}")
def update_attribute_definition(
    attr_id: str,
    req: AttributeUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_tprm_admin)
):
    attr = db.query(VendorAttributeDefinition).filter_by(id=attr_id).first()
    if not attr:
        raise HTTPException(status_code=404, detail="Attribute not found.")

    if req.is_active is False and attr.is_workflow_driver:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot deactivate '{attr.key_name}' because it is an active workflow routing driver (Section 6.9)."
        )

    if req.description_key is not None:
        attr.description_key = req.description_key
    if req.add_option and req.add_option.strip():
        opts = list(attr.options or [])
        if req.add_option.strip() not in opts:
            opts.append(req.add_option.strip())
            attr.options = opts
    if req.is_active is not None:
        attr.is_active = req.is_active
    attr.last_reviewed_at = datetime.now(timezone.utc)

    AuditService.log_event(
        db,
        actor_email=current_user["email"],
        action="ATTRIBUTE_UPDATED",
        entity_type="ATTRIBUTE",
        entity_id=attr.id,
        details={"key_name": attr.key_name, "options": attr.options, "is_active": attr.is_active}
    )
    db.commit()
    return {"status": "updated", "id": attr.id, "options": attr.options, "is_active": attr.is_active}

@router.get("/{vendor_id}")
def get_vendor(
    vendor_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return VendorService.get_vendor_details(db, vendor_id)

@router.put("/{vendor_id}")
def update_vendor(
    vendor_id: str,
    req: VendorUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    req_data = getattr(req, "model_dump", req.dict)(exclude_unset=True)
    v = VendorService.update_vendor(db, vendor_id, req_data, actor_email=current_user["email"])
    return {"status": "updated", "vendor_id": v.id}

@router.post("/{vendor_id}/renew")
def record_renewal_decision(
    vendor_id: str,
    req: RenewalDecisionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_tprm_admin)
):
    v = db.query(Vendor).filter_by(id=vendor_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Vendor not found.")

    open_findings = db.query(RiskFinding).filter_by(vendor_id=v.id, status="Open").count()
    days = 365 if v.vendor_tier == "Tier 1" else 730
    next_date = (datetime.now(timezone.utc) + timedelta(days=days)).date()

    ren = RenewalDecision(
        vendor_id=v.id,
        decision=req.decision,
        decided_by=current_user["email"],
        rationale=req.rationale,
        open_findings_at_decision=str(open_findings),
        next_renewal_date=next_date,
    )
    db.add(ren)
    v.renewal_status = req.decision

    if "Offboard" in req.decision or "Non-Renewal" in req.decision:
        WorkflowEngine.initiate_offboarding(db, v, actor_email=current_user["email"], reason=req.rationale)

    AuditService.log_event(
        db,
        actor_email=current_user["email"],
        action="VENDOR_RENEWAL_DECIDED",
        entity_type="VENDOR",
        entity_id=v.id,
        details={"decision": req.decision, "rationale": req.rationale, "open_findings": open_findings}
    )
    db.commit()
    return {"status": "renewal_recorded", "decision": req.decision, "next_renewal_date": next_date.isoformat()}

@router.post("/{vendor_id}/offboard")
def offboard_vendor(
    vendor_id: str,
    req: OffboardRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_tprm_admin)
):
    v_model = db.query(Vendor).filter_by(id=vendor_id).first()
    if not v_model:
        raise HTTPException(status_code=404, detail="Vendor not found")
    WorkflowEngine.initiate_offboarding(db, v_model, actor_email=current_user["email"], reason=req.reason)
    return {"status": "offboarding_initiated", "vendor_id": vendor_id, "stage": v_model.current_stage}

@router.post("/{vendor_id}/close")
def close_vendor(
    vendor_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_tprm_admin)
):
    v_model = db.query(Vendor).filter_by(id=vendor_id).first()
    if not v_model:
        raise HTTPException(status_code=404, detail="Vendor not found")
    WorkflowEngine.close_vendor(db, v_model, actor_email=current_user["email"])
    return {"status": "closed", "vendor_id": vendor_id, "stage": "Closed"}

@router.post("/{vendor_id}/archive")
def archive_vendor(
    vendor_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_tprm_admin)
):
    v_model = db.query(Vendor).filter_by(id=vendor_id).first()
    if not v_model:
        raise HTTPException(status_code=404, detail="Vendor not found")
    WorkflowEngine.archive_vendor(db, v_model, actor_email=current_user["email"])
    return {"status": "archived", "vendor_id": vendor_id, "is_archived": True}
