"""Vendor management service with Table 9 attribute validation and CRUD operations.

Source Authority: Cadence_TPRM_Training.docx Section 2.1, 4.1, 5.2, Table 4, Table 9.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.cadence_tprm.models.vendor import Vendor, Contract
from src.cadence_tprm.models.assessment import Assessment
from src.cadence_tprm.models.task import Task
from src.cadence_tprm.models.assessment import RiskFinding
from src.cadence_tprm.services.workflow_engine import WorkflowEngine
from src.cadence_tprm.services.audit_service import AuditService

ALLOWED_CATEGORIES = {
    "Service Provider and Vendor",
    "Revenue Partner",
    "Marketing Partner",
    "Staffing Vendor",
    "International Vendor",
}

ALLOWED_TIERS = {"Tier 1", "Tier 2", "Tier 3"}

ALLOWED_TYPES = {
    "Consulting",
    "Operations",
    "Regulatory",
    "Strategic",
    "Technology",
    "Unknown",
}

ALLOWED_CRITICALITIES = {"Critical", "High", "Medium", "Low"}

class VendorService:

    @staticmethod
    def validate_attributes(data: dict):
        """Strict validation against Table 9 attributes."""
        name = data.get("name")
        if not name or not str(name).strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vendor name is required.")

        category = data.get("vendor_category")
        if category not in ALLOWED_CATEGORIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid vendor_category '{category}'. Allowed: {sorted(list(ALLOWED_CATEGORIES))}"
            )

        tier = data.get("vendor_tier")
        if tier not in ALLOWED_TIERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid vendor_tier '{tier}'. Allowed: {sorted(list(ALLOWED_TIERS))}"
            )

        v_type = data.get("type", "Technology")
        if v_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid type '{v_type}'. Allowed: {sorted(list(ALLOWED_TYPES))}"
            )

        crit = data.get("criticality", "Medium")
        if crit not in ALLOWED_CRITICALITIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid criticality '{crit}'. Allowed: {sorted(list(ALLOWED_CRITICALITIES))}"
            )

        pvc = data.get("primary_vendor_contact")
        if not pvc or "@" not in str(pvc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valid primary_vendor_contact email is required.")

        bo = data.get("business_owner")
        if not bo or "@" not in str(bo):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valid business_owner email is required.")

    @staticmethod
    def create_vendor(db: Session, data: dict, actor_email: str) -> Vendor:
        VendorService.validate_attributes(data)

        # Check for duplicate vendor name
        existing = db.query(Vendor).filter_by(name=data["name"].strip()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A vendor with name '{data['name']}' already exists."
            )

        vendor = Vendor(
            name=data["name"].strip(),
            type=data.get("type", "Technology"),
            criticality=data.get("criticality", "Medium"),
            primary_vendor_contact=data["primary_vendor_contact"].strip().lower(),
            business_owner=data["business_owner"].strip().lower(),
            vendor_tier=data["vendor_tier"],
            vendor_category=data["vendor_category"],
            website=data.get("website", ""),
            lifecycle_status="New",
            current_workflow_name="CD_Onboarding Workflow",
            current_stage="New Third Party"
        )
        db.add(vendor)
        db.flush()

        # Audit vendor creation
        AuditService.log_event(
            db,
            actor_email=actor_email,
            action="VENDOR_CREATED",
            entity_type="VENDOR",
            entity_id=vendor.id,
            details={"name": vendor.name, "category": vendor.vendor_category, "tier": vendor.vendor_tier}
        )

        # Auto-trigger onboarding state machine
        WorkflowEngine.route_new_vendor(db, vendor, actor_email)

        return vendor

    @staticmethod
    def list_vendors(
        db: Session,
        category: Optional[str] = None,
        tier: Optional[str] = None,
        lifecycle_status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        query = db.query(Vendor)

        if category:
            query = query.filter(Vendor.vendor_category == category)
        if tier:
            query = query.filter(Vendor.vendor_tier == tier)
        if lifecycle_status:
            query = query.filter(Vendor.lifecycle_status == lifecycle_status)
        if search:
            s = f"%{search.strip()}%"
            query = query.filter(
                (Vendor.name.ilike(s)) |
                (Vendor.primary_vendor_contact.ilike(s)) |
                (Vendor.business_owner.ilike(s))
            )

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(Vendor.created_at.desc()).offset(offset).limit(page_size).all()

        return {
            "items": [
                {
                    "id": v.id,
                    "name": v.name,
                    "type": v.type,
                    "criticality": v.criticality,
                    "primary_vendor_contact": v.primary_vendor_contact,
                    "business_owner": v.business_owner,
                    "vendor_tier": v.vendor_tier,
                    "vendor_category": v.vendor_category,
                    "website": v.website,
                    "lifecycle_status": v.lifecycle_status,
                    "current_workflow_name": v.current_workflow_name,
                    "current_stage": v.current_stage,
                    "last_assessment_completion_date": v.last_assessment_completion_date.isoformat() if v.last_assessment_completion_date else None,
                    "next_reassessment_due_date": v.next_reassessment_due_date.isoformat() if v.next_reassessment_due_date else None,
                    "created_at": v.created_at.isoformat(),
                }
                for v in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size
        }

    @staticmethod
    def get_vendor_details(db: Session, vendor_id: str) -> dict:
        vendor = db.query(Vendor).filter_by(id=vendor_id).first()
        if not vendor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found.")

        assessments = db.query(Assessment).filter_by(vendor_id=vendor.id).order_by(Assessment.created_at.desc()).all()
        findings = db.query(RiskFinding).filter_by(vendor_id=vendor.id).all()
        contracts = db.query(Contract).filter_by(vendor_id=vendor.id).all()
        tasks = db.query(Task).filter_by(vendor_id=vendor.id).all()

        return {
            "vendor": {
                "id": vendor.id,
                "name": vendor.name,
                "type": vendor.type,
                "criticality": vendor.criticality,
                "primary_vendor_contact": vendor.primary_vendor_contact,
                "business_owner": vendor.business_owner,
                "vendor_tier": vendor.vendor_tier,
                "vendor_category": vendor.vendor_category,
                "website": vendor.website,
                "lifecycle_status": vendor.lifecycle_status,
                "current_workflow_name": vendor.current_workflow_name,
                "current_stage": vendor.current_stage,
                "last_assessment_completion_date": vendor.last_assessment_completion_date.isoformat() if vendor.last_assessment_completion_date else None,
                "next_reassessment_due_date": vendor.next_reassessment_due_date.isoformat() if vendor.next_reassessment_due_date else None,
                "created_at": vendor.created_at.isoformat(),
            },
            "assessments": [
                {
                    "id": a.id,
                    "template_code": a.template_code,
                    "status": a.status,
                    "overall_score": a.overall_score,
                    "due_date": a.due_date.isoformat() if a.due_date else None,
                    "completed_at": a.completed_at.isoformat() if a.completed_at else None,
                    "decision_reason": a.decision_reason,
                    "decision_by": a.decision_by,
                }
                for a in assessments
            ],
            "findings": [
                {
                    "id": f.id,
                    "rule_code": f.rule_code,
                    "risk_name": f.risk_name,
                    "inherent_risk": f.inherent_risk,
                    "control_id": f.control_id,
                    "control_name": f.control_name,
                    "responsible_group": f.responsible_group,
                    "status": f.status,
                    "mitigation_recommendation": f.mitigation_recommendation,
                    "due_date": f.due_date.isoformat() if f.due_date else None,
                }
                for f in findings
            ],
            "contracts": [
                {
                    "id": c.id,
                    "contract_reference": c.contract_reference,
                    "title": c.title,
                    "source": c.source,
                    "status": c.status,
                    "effective_date": c.effective_date.isoformat() if c.effective_date else None,
                    "expiration_date": c.expiration_date.isoformat() if c.expiration_date else None,
                }
                for c in contracts
            ],
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "task_type": t.task_type,
                    "status": t.status,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                    "assignee_email": t.assignee_email,
                    "collaborator_group": t.collaborator_group,
                }
                for t in tasks
            ]
        }
