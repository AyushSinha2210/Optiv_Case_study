"""Immutable, tamper-evident audit logging model.

Source Authority: Cadence_TPRM_Training.docx Section 1.2, 2.4.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, JSON
from src.cadence_tprm.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    actor_email = Column(String(255), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)  # e.g. VENDOR_CREATED, ASSESSMENT_APPROVED
    entity_type = Column(String(100), nullable=False, index=True)  # VENDOR, ASSESSMENT, WORKFLOW
    entity_id = Column(String(100), nullable=False, index=True)
    details = Column(JSON, nullable=False)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
