"""Workflow definitions, Appendix A rule specs, Appendix D SLAs, cloning, and transition endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.cadence_tprm.database import get_db
from src.cadence_tprm.models.workflow import Workflow, WorkflowRuleSpec, SLAConfig, WorkflowTransition
from src.cadence_tprm.models.vendor import Vendor
from src.cadence_tprm.models.assessment import Assessment
from src.cadence_tprm.services.workflow_engine import WorkflowEngine
from src.cadence_tprm.services.audit_service import AuditService
from src.cadence_tprm.services.auth_service import get_current_user, require_tprm_admin

router = APIRouter(prefix="/workflows", tags=["Workflows"])

class WorkflowTransitionRequest(BaseModel):
    action: str  # Approve, Reject, Offboard, Close
    actor_email: Optional[str] = None
    decision_reason: str = "Workflow transition executed"

class WorkflowCloneRequest(BaseModel):
    source_workflow_name: str
    new_workflow_name: str
    description: Optional[str] = None

@router.get("")
def list_workflows(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    workflows = db.query(Workflow).all()
    all_rules = db.query(WorkflowRuleSpec).all()
    slas = db.query(SLAConfig).all()

    items = []
    for w in workflows:
        wf_rules = [
            {
                "rule_code": r.rule_code,
                "source_sr_no": r.source_sr_no,
                "rule_name": r.rule_name,
                "stage_name": r.stage_name,
                "trigger_name": r.trigger_name,
                "trigger_type": r.trigger_type,
                "rule_type": r.rule_type,
                "description": r.description,
                "condition_expression": r.condition_expression,
                "action_expression": r.action_expression,
                "discrepancy_note": r.discrepancy_note,
            }
            for r in all_rules
            if r.workflow_name == w.name
        ]
        items.append({
            "id": w.id,
            "name": w.name,
            "description": w.description,
            "status": w.status,
            "is_default": w.is_default,
            "is_active": w.is_active,
            "stages": w.stages or [],
            "rules": wf_rules,
            "instances_count": len(w.instances),
        })

    reassessment_rules = [
        {
            "rule_code": r.rule_code,
            "rule_name": r.rule_name,
            "trigger_type": r.trigger_type,
            "description": r.description,
            "condition_expression": r.condition_expression,
            "action_expression": r.action_expression,
        }
        for r in all_rules
        if r.workflow_name == "TPRM Reassessment Rules"
    ]

    sla_items = [
        {
            "sla_no": s.sla_no,
            "sla_name": s.sla_name,
            "description": s.description,
            "timeline_days": s.timeline_days,
            "effective_deadline_days": s.effective_deadline_days,
            "reminder_days": s.reminder_days,
        }
        for s in slas
    ]

    return {
        "items": items,
        "workflows": items,
        "reassessment_rules": reassessment_rules,
        "slas": sla_items,
    }

@router.post("/clone", status_code=status.HTTP_201_CREATED)
def clone_workflow(
    req: WorkflowCloneRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_tprm_admin)
):
    """Implements Section 6.4 Workflow Cloning into Draft status."""
    src = db.query(Workflow).filter_by(name=req.source_workflow_name).first()
    if not src:
        raise HTTPException(status_code=404, detail="Source workflow not found.")
    if db.query(Workflow).filter_by(name=req.new_workflow_name.strip()).first():
        raise HTTPException(status_code=400, detail="Workflow with that name already exists.")

    cloned = Workflow(
        name=req.new_workflow_name.strip(),
        description=req.description or f"Cloned draft from {src.name}",
        status="Draft",
        is_default=False,
        is_active=True,
        stages=list(src.stages or []),
        created_by=current_user["email"],
    )
    db.add(cloned)
    AuditService.log_event(
        db,
        actor_email=current_user["email"],
        action="WORKFLOW_CLONED",
        entity_type="WORKFLOW",
        entity_id=cloned.id,
        details={"source_workflow": src.name, "new_workflow": cloned.name, "status": "Draft"}
    )
    db.commit()
    return {"status": "cloned", "id": cloned.id, "name": cloned.name, "workflow_status": cloned.status}

@router.post("/instances/{vendor_id}/transition")
def execute_workflow_transition(
    vendor_id: str,
    req: WorkflowTransitionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_tprm_admin)
):
    """Executes an authorized workflow transition (Approve, Reject, Offboard, Close) for a vendor."""
    vendor = db.query(Vendor).filter_by(id=vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found.")

    asm = db.query(Assessment).filter_by(vendor_id=vendor.id).order_by(Assessment.created_at.desc()).first()
    act = req.action.strip().lower()
    actor = current_user["email"]

    if act == "approve":
        if not asm:
            raise HTTPException(status_code=400, detail="No assessment found for vendor.")
        WorkflowEngine.approve_vendor(db, vendor, asm, actor_email=actor, reason=req.decision_reason)
    elif act == "reject":
        if not asm:
            raise HTTPException(status_code=400, detail="No assessment found for vendor.")
        WorkflowEngine.reject_vendor(db, vendor, asm, actor_email=actor, reason=req.decision_reason)
    elif act == "offboard":
        WorkflowEngine.initiate_offboarding(db, vendor, actor_email=actor, reason=req.decision_reason)
    elif act == "close":
        WorkflowEngine.close_vendor(db, vendor, actor_email=actor, reason=req.decision_reason)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported transition action '{req.action}'.")

    return {
        "status": "transitioned",
        "vendor_id": vendor.id,
        "lifecycle_status": vendor.lifecycle_status,
        "current_stage": vendor.current_stage,
    }

@router.get("/transitions")
def list_transitions(limit: int = 50, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    transitions = (
        db.query(WorkflowTransition)
        .order_by(WorkflowTransition.timestamp.desc())
        .limit(limit)
        .all()
    )
    items = [
        {
            "id": t.id,
            "actor_email": t.actor_email,
            "from_stage": t.from_stage,
            "to_stage": t.to_stage,
            "trigger_name": t.trigger_name,
            "rule_name": t.rule_name,
            "decision_reason": t.decision_reason,
            "timestamp": t.timestamp.isoformat(),
        }
        for t in transitions
    ]
    return {"items": items, "transitions": items}
