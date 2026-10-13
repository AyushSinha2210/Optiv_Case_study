"""Workflow definitions and transition history endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.cadence_tprm.database import get_db
from src.cadence_tprm.models.workflow import Workflow, WorkflowTransition
from src.cadence_tprm.services.auth_service import get_current_user

router = APIRouter(prefix="/workflows", tags=["Workflows"])

@router.get("")
def list_workflows(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    workflows = db.query(Workflow).all()
    return {
        "workflows": [
            {
                "id": w.id,
                "name": w.name,
                "description": w.description,
                "is_active": w.is_active,
                "instances_count": len(w.instances),
            }
            for w in workflows
        ]
    }

@router.get("/transitions")
def list_transitions(limit: int = 50, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    transitions = (
        db.query(WorkflowTransition)
        .order_by(WorkflowTransition.timestamp.desc())
        .limit(limit)
        .all()
    )
    return {
        "transitions": [
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
    }
