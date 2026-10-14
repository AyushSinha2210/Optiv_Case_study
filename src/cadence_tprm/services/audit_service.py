"""Audit service for append-only, tamper-evident action logging."""

from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session
from src.cadence_tprm.models.audit import AuditLog

_SENSITIVE_KEY_PARTS = (
    "password", "secret", "token", "authorization", "cookie",
    "payload", "body", "document", "raw", "value", "ssn", "pan",
    "card", "contact", "email", "address",
)


def sanitize_audit_details(value: Any, key: str = "") -> Any:
    """Return a recursively sanitized audit projection."""
    if any(part in key.lower() for part in _SENSITIVE_KEY_PARTS):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {
            str(k): sanitize_audit_details(v, str(k))
            for k, v in value.items()
            if str(k).lower() not in {"payload", "raw_payload", "request_body"}
        }
    if isinstance(value, (list, tuple)):
        return [sanitize_audit_details(item, key) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)[:256]


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
        """Append a sanitized audit record to the persistent log."""
        log_entry = AuditLog(
            actor_email=actor_email,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            details=sanitize_audit_details(details or {}),
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
