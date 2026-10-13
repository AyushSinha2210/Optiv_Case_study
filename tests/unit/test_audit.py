"""Unit tests for sanitized audit trail subsystem and leakage prevention."""

import json
import pytest
from src.pii_guard.orchestration.state import PipelineStage
from src.pii_guard.reporting.audit import AuditEvent, AuditTrail


def test_audit_event_immutability():
    """AuditEvent is frozen and cannot be modified after instantiation."""
    event = AuditEvent(
        document_id="doc-test-123",
        stage=PipelineStage.EXTRACTED,
        event_type="STAGE_EXIT",
        status="success",
    )
    with pytest.raises(Exception):
        event.status = "failure"


def test_audit_trail_record_and_filter():
    """AuditTrail accurately records events and filters by document ID."""
    trail = AuditTrail()
    trail.record_event(
        document_id="doc-aaa",
        stage=PipelineStage.RECEIVED,
        event_type="DOCUMENT_INGESTED",
        status="success",
    )
    trail.record_event(
        document_id="doc-bbb",
        stage=PipelineStage.RECEIVED,
        event_type="DOCUMENT_INGESTED",
        status="success",
    )
    trail.record_event(
        document_id="doc-aaa",
        stage=PipelineStage.VERIFIED,
        event_type="VERIFICATION_EVALUATED",
        status="success",
        verification_status="PASS",
        release_decision=True,
    )

    events_aaa = trail.get_events(document_id="doc-aaa")
    events_bbb = trail.get_events(document_id="doc-bbb")

    assert len(events_aaa) == 2
    assert len(events_bbb) == 1
    assert events_aaa[1].release_decision is True


def test_audit_event_sanitization_zero_leakage():
    """Verify that sensitive canaries and absolute paths are scrubbed in audit records."""
    trail = AuditTrail()
    canary_path = "D:\\Confidential\\Payroll\\canary_doc.pdf"
    canary_email = "victim.canary@leakage-test.org"

    event = trail.record_event(
        document_id="doc-sec-999",
        stage=PipelineStage.FAILED,
        event_type="STAGE_FAILED",
        status="failure",
        error_code="ERR_EXTRACTION_FAILED",
        message=f"Crash while opening {canary_path} for user {canary_email}",
    )

    serialized = event.to_safe_dict()
    dumped_json = json.dumps(serialized)

    assert "D:\\Confidential" not in dumped_json
    assert "victim.canary@leakage-test.org" not in dumped_json
    assert "[REDACTED_PATH]" in dumped_json
    assert "[REDACTED_EMAIL]" in dumped_json


def test_audit_export_conforms_to_schema():
    """Exported audit log entries match allowlisted metadata keys only."""
    trail = AuditTrail()
    trail.record_event(
        document_id="doc-001",
        stage=PipelineStage.RELEASED,
        event_type="RELEASE_DECIDED",
        status="success",
        duration_sec=0.1425,
        entity_count=3,
        category_counts={"EMAIL": 1, "PERSON": 2},
        verification_status="PASS",
        release_decision=True,
    )

    exported = trail.export_sanitized_log("doc-001")
    assert len(exported) == 1
    rec = exported[0]

    assert rec["document_id"] == "doc-001"
    assert rec["stage"] == "RELEASED"
    assert rec["category_counts"] == {"EMAIL": 1, "PERSON": 2}
    assert rec["release_decision"] is True
    assert "raw_text" not in rec
    assert "entities" not in rec
