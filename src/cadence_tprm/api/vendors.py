"""Vendor management endpoints with strict Table 9 attributes."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from src.cadence_tprm.database import get_db
from src.cadence_tprm.services.vendor_service import VendorService
from src.cadence_tprm.services.workflow_engine import WorkflowEngine
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

class OffboardRequest(BaseModel):
    reason: str

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
    vendor = VendorService.create_vendor(db, req.model_dump(), actor_email=current_user["email"])
    return {
        "status": "created",
        "vendor_id": vendor.id,
        "name": vendor.name,
        "workflow": vendor.current_workflow_name,
        "stage": vendor.current_stage,
        "lifecycle_status": vendor.lifecycle_status
    }

@router.get("/{vendor_id}")
def get_vendor(
    vendor_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return VendorService.get_vendor_details(db, vendor_id)

@router.post("/{vendor_id}/offboard")
def offboard_vendor(
    vendor_id: str,
    req: OffboardRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_tprm_admin)
):
    vendor = VendorService.get_vendor_details(db, vendor_id)["vendor"]
    # Re-fetch model instance for updates
    from src.cadence_tprm.models.vendor import Vendor
    v_model = db.query(Vendor).filter_by(id=vendor_id).first()
    WorkflowEngine.initiate_offboarding(db, v_model, actor_email=current_user["email"], reason=req.reason)
    return {"status": "offboarding_initiated", "vendor_id": vendor_id}

@router.post("/{vendor_id}/close")
def close_vendor(
    vendor_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_tprm_admin)
):
    from src.cadence_tprm.models.vendor import Vendor
    v_model = db.query(Vendor).filter_by(id=vendor_id).first()
    if not v_model:
        raise HTTPException(status_code=404, detail="Vendor not found")
    WorkflowEngine.close_vendor(db, v_model, actor_email=current_user["email"])
    return {"status": "closed", "vendor_id": vendor_id}
