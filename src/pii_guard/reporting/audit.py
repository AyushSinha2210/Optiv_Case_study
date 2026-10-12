"""Sanitized audit trail subsystem.

PRIVACY MANDATE:
Audit records store exclusively safe metadata, lifecycle stage timings, entity category counts,
and authorization decisions. They MUST NEVER retain raw document text, matched PII values,
internal filesystem paths, or credentials.
"""

import uuid
import threading
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict

from ..orchestration.state import PipelineStage
from ..orchestration.errors import sanitize_error_message


class AuditEvent(BaseModel):
    """Structured, immutable audit record."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    event_id: str = Field(
        default_factory=lambda: f"evt-{uuid.uuid4().hex[:12]}",
        description="Unique audit event identifier"
    )
    document_id: str = Field(..., description="Unique document UUID")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timezone-aware UTC event timestamp"
    )
    stage: PipelineStage = Field(..., description="Pipeline lifecycle stage")
    event_type: str = Field(
        ..., description="Standardized event type (e.g. STAGE_ENTER, VERIFICATION_EVALUATED, RELEASE_DECIDED)"
    )
    status: str = Field(..., description="Outcome: success, failure, blocked, incomplete")
    error_code: Optional[str] = Field(default=None, description="Safe machine-readable code")
    duration_sec: Optional[float] = Field(default=None, ge=0.0, description="Duration in seconds")
    entity_count: Optional[int] = Field(default=None, ge=0, description="Total entity count if applicable")
    category_counts: Dict[str, int] = Field(
        default_factory=dict, description="Counts grouped by standard PII category"
    )
    verification_status: Optional[str] = Field(default=None, description="PASS, FAIL, or INCOMPLETE")
    release_decision: bool = Field(default=False, description="Release gate authorization decision")
    report_ref: Optional[str] = Field(default=None, description="Opaque report identifier")
    safe_message: Optional[str] = Field(default=None, description="Scrubbed status note")

    def to_safe_dict(self) -> Dict[str, Any]:
        """Serialize record strictly to allowlisted metadata fields."""
        return {
            "event_id": self.event_id,
            "document_id": self.document_id,
            "timestamp": self.timestamp.isoformat(),
            "stage": self.stage.value,
            "event_type": self.event_type,
            "status": self.status,
            "error_code": self.error_code,
            "duration_sec": round(self.duration_sec, 4) if self.duration_sec is not None else None,
            "entity_count": self.entity_count,
            "category_counts": dict(self.category_counts),
            "verification_status": self.verification_status,
            "release_decision": self.release_decision,
            "report_ref": self.report_ref,
            "safe_message": self.safe_message,
        }


class AuditTrail:
    """Thread-safe ledger of audit events for document processing."""

    def __init__(self):
        self._lock = threading.Lock()
        self._events: List[AuditEvent] = []

    def record_event(
        self,
        document_id: str,
        stage: PipelineStage,
        event_type: str,
        status: str,
        error_code: Optional[str] = None,
        duration_sec: Optional[float] = None,
        entity_count: Optional[int] = None,
        category_counts: Optional[Dict[str, int]] = None,
        verification_status: Optional[str] = None,
        release_decision: bool = False,
        report_ref: Optional[str] = None,
        message: Optional[str] = None,
    ) -> AuditEvent:
        """Create and store an immutable, sanitized audit event."""
        event = AuditEvent(
            document_id=document_id,
            stage=stage,
            event_type=event_type,
            status=status,
            error_code=error_code,
            duration_sec=duration_sec,
            entity_count=entity_count,
            category_counts=category_counts or {},
            verification_status=verification_status,
            release_decision=release_decision,
            report_ref=report_ref,
            safe_message=sanitize_error_message(message) if message else None,
        )
        with self._lock:
            self._events.append(event)
        return event

    def get_events(self, document_id: Optional[str] = None) -> List[AuditEvent]:
        """Retrieve audit events, optionally filtered by document_id."""
        with self._lock:
            if document_id is None:
                return list(self._events)
            return [e for e in self._events if e.document_id == document_id]

    def clear(self) -> None:
        """Clear recorded events (primarily for test fixture isolation)."""
        with self._lock:
            self._events.clear()

    def export_sanitized_log(self, document_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Export serialized event list matching strict sanitization rules."""
        events = self.get_events(document_id=document_id)
        return [e.to_safe_dict() for e in events]


# Global audit instance for application-wide logging
_GLOBAL_AUDIT_TRAIL = AuditTrail()


def get_global_audit_trail() -> AuditTrail:
    """Return the global audit trail instance."""
    return _GLOBAL_AUDIT_TRAIL
