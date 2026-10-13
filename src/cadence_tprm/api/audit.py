"""Audit trail query endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.cadence_tprm.database import get_db
from src.cadence_tprm.services.audit_service import AuditService
from src.cadence_tprm.services.auth_service import get_current_user

router = APIRouter(prefix="/audit", tags=["Audit"])

@router.get("")
def list_audit_logs(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    norm_type = entity_type.upper() if entity_type and entity_type != "All" else None
    logs = AuditService.list_logs(db, entity_type=norm_type, entity_id=entity_id, limit=limit)
    items = [
        {
            "id": log.id,
            "actor_email": log.actor_email,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "details": log.details,
            "timestamp": log.timestamp.isoformat(),
        }
        for log in logs
    ]
    return {"logs": items, "items": items, "total": len(items)}
