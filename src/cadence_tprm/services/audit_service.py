"""Audit service for append-only, tamper-evident action logging."""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src.cadence_tprm.models.audit import AuditLog

class AuditService:
    @staticmethod
    def log_event(
        db: Session,
        actor_email: str,
        action: str,
        entity_type: str,
        entity_id: str,
        details: dict,
        ip_address: str = None
    ) -> AuditLog:
        """Appends a new audit record to the persistent log."""
        log_entry = AuditLog(
            actor_email=actor_email,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            details=details or {},
            ip_address=ip_address,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry

    @staticmethod
    def list_logs(db: Session, entity_type: str = None, entity_id: str = None, limit: int = 100):
        query = db.query(AuditLog)
        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.filter(AuditLog.entity_id == str(entity_id))
        return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
