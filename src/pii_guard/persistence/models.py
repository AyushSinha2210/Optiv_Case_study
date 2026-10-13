"""Persistent storage models for PII Guard runs, findings, and audit records."""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from src.cadence_tprm.database import Base


class PIIProcessingRun(Base):
    """Persistent execution record for document PII protection runs."""
    __tablename__ = "pii_processing_runs"

    document_id = Column(String(64), primary_key=True, index=True)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(32), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    integrity_hash = Column(String(64), nullable=True)
    workflow_status = Column(String(32), default="pending", index=True)
    current_stage = Column(String(32), default="RECEIVED")
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    duration_sec = Column(Float, default=0.0)
    pages_count = Column(Integer, default=1)
    char_count = Column(Integer, default=0)
    extraction_status = Column(String(32), default="pending")
    detection_status = Column(String(32), default="pending")
    redaction_status = Column(String(32), default="pending")
    verification_status = Column(String(32), default="pending", index=True)
    release_allowed = Column(Boolean, default=False, index=True)
    category_counts_json = Column(Text, default="{}")
    redactions_applied = Column(Integer, default=0)
    safe_warnings_json = Column(Text, default="[]")
    safe_error = Column(Text, nullable=True)
    safe_error_code = Column(String(64), nullable=True)
    artifact_ref = Column(String(128), nullable=True)
    original_ref = Column(String(128), nullable=True)
    extracted_text = Column(Text, nullable=True)
    redacted_text = Column(Text, nullable=True)
    stage_history_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    findings = relationship("PIIFinding", back_populates="run", cascade="all, delete-orphan")
    audit_events = relationship("PIIAuditRecord", back_populates="run", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """Convert database record to dictionary matching API schemas."""
        cat_counts = {}
        try:
            cat_counts = json.loads(self.category_counts_json or "{}")
        except Exception:
            pass

        stages = []
        try:
            stages = json.loads(self.stage_history_json or "[]")
        except Exception:
            pass

        warnings = []
        try:
            warnings = json.loads(self.safe_warnings_json or "[]")
        except Exception:
            pass

        return {
            "document_id": self.document_id,
            "original_filename": self.original_filename,
            "file_type": self.file_type,
            "file_size_bytes": self.file_size_bytes,
            "integrity_hash": self.integrity_hash,
            "workflow_status": self.workflow_status,
            "current_stage": self.current_stage,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_sec": self.duration_sec,
            "pages_count": self.pages_count,
            "char_count": self.char_count,
            "extraction_status": self.extraction_status,
            "detection_status": self.detection_status,
            "redaction_status": self.redaction_status,
            "verification_status": self.verification_status,
            "release_allowed": self.release_allowed,
            "category_counts": cat_counts,
            "redactions_applied": self.redactions_applied,
            "safe_warnings": warnings,
            "safe_error": self.safe_error,
            "safe_error_code": self.safe_error_code,
            "artifact_ref": self.artifact_ref,
            "original_ref": self.original_ref,
            "extracted_text": self.extracted_text,
            "redacted_text": self.redacted_text,
            "stage_history": stages,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PIIFinding(Base):
    """Detailed finding entry for each detected sensitive PII instance."""
    __tablename__ = "pii_findings"

    id = Column(String(64), primary_key=True)
    document_id = Column(String(64), ForeignKey("pii_processing_runs.document_id"), nullable=False, index=True)
    finding_index = Column(Integer, default=0)
    entity_type = Column(String(64), nullable=False, index=True)
    start_offset = Column(Integer, nullable=False)
    end_offset = Column(Integer, nullable=False)
    confidence = Column(Float, default=1.0)
    value_masked = Column(String(255), nullable=True)
    replacement_mask = Column(String(255), nullable=True)
    detector_method = Column(String(64), default="regex_rule")
    rule_id = Column(String(64), default="POLICY_DEFAULT")
    rationale = Column(Text, nullable=True)
    status = Column(String(32), default="MASKED")  # MASKED, PRESERVED, FLAGGED, MANUAL_REVIEW
    verification_result = Column(String(32), default="VERIFIED_REMOVED")
    page_or_slide = Column(Integer, default=1)
    risk_level = Column(String(32), default="HIGH")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    run = relationship("PIIProcessingRun", back_populates="findings")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "document_id": self.document_id,
            "finding_index": self.finding_index,
            "type": self.entity_type,
            "start": self.start_offset,
            "end": self.end_offset,
            "confidence": self.confidence,
            "value": self.value_masked,
            "masked_value": self.replacement_mask,
            "detector_method": self.detector_method,
            "rule_id": self.rule_id,
            "rationale": self.rationale,
            "status": self.status,
            "verification_result": self.verification_result,
            "page_or_slide": self.page_or_slide,
            "risk_level": self.risk_level,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PIIAuditRecord(Base):
    """Persistent immutable audit trail event."""
    __tablename__ = "pii_audit_records"

    id = Column(String(64), primary_key=True)
    event_id = Column(String(64), index=True)
    document_id = Column(String(64), ForeignKey("pii_processing_runs.document_id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    stage = Column(String(32), nullable=False)
    event_type = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False)
    error_code = Column(String(64), nullable=True)
    duration_sec = Column(Float, nullable=True)
    entity_count = Column(Integer, nullable=True)
    category_counts_json = Column(Text, default="{}")
    verification_status = Column(String(32), nullable=True)
    release_decision = Column(Boolean, default=False)
    report_ref = Column(String(64), nullable=True)
    safe_message = Column(Text, nullable=True)
    actor = Column(String(64), default="SYSTEM_PII_GUARD")

    run = relationship("PIIProcessingRun", back_populates="audit_events")

    def to_dict(self) -> Dict[str, Any]:
        cat_counts = {}
        try:
            cat_counts = json.loads(self.category_counts_json or "{}")
        except Exception:
            pass

        return {
            "id": self.id,
            "event_id": self.event_id,
            "document_id": self.document_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "stage": self.stage,
            "event_type": self.event_type,
            "status": self.status,
            "error_code": self.error_code,
            "duration_sec": self.duration_sec,
            "entity_count": self.entity_count,
            "category_counts": cat_counts,
            "verification_status": self.verification_status,
            "release_decision": self.release_decision,
            "report_ref": self.report_ref,
            "safe_message": self.safe_message,
            "actor": self.actor,
        }
