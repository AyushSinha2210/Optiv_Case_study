"""Integration tests for end-to-end orchestration pipeline coordinator (Member 5 - Tirth)."""

from pathlib import Path
import pytest

from src.pii_guard.orchestration.pipeline import process_document
from src.pii_guard.orchestration.state import PipelineStage
from src.pii_guard.reporting.audit import AuditTrail
from src.pii_guard.orchestration.artifacts import ArtifactManager

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "ingestion"
DEMO_DIR = Path(__file__).resolve().parent.parent.parent / "demo_samples" / "fixtures"


def test_orchestration_clean_text_success(tmp_path):
    """Clean plain text document processes end-to-end through RELEASED stage."""
    doc_path = DEMO_DIR / "04_clean_no_pii.txt"
    trail = AuditTrail()
    art_mgr = ArtifactManager(storage_dir=tmp_path / "artifacts")

    result = process_document(
        str(doc_path),
        audit_trail=trail,
        artifact_manager=art_mgr,
    )

    assert result.workflow_status == "success"
    assert result.current_stage == PipelineStage.RELEASED
    assert result.release_allowed is True
    assert result.verification_status == "PASS"
    assert result.artifact_ref is not None

    # Verify audit events recorded all stages
    events = trail.get_events(result.document_id)
    stages_recorded = [e.stage for e in events]
    assert PipelineStage.RECEIVED in stages_recorded
    assert PipelineStage.EXTRACTED in stages_recorded
    assert PipelineStage.DETECTED in stages_recorded
    assert PipelineStage.REDACTED in stages_recorded
    assert PipelineStage.VERIFIED in stages_recorded
    assert PipelineStage.RELEASED in stages_recorded


def test_orchestration_synthetic_pii_document_release(tmp_path):
    """Document with synthetic email and phone is masked, verified, and released."""
    doc_path = DEMO_DIR / "01_synthetic_email.txt"
    trail = AuditTrail()
    art_mgr = ArtifactManager(storage_dir=tmp_path / "artifacts")

    result = process_document(
        str(doc_path),
        audit_trail=trail,
        artifact_manager=art_mgr,
    )

    assert result.workflow_status == "success"
    assert result.release_allowed is True
    assert result.verification_status == "PASS"
    assert result.redactions_applied >= 1
    assert "EMAIL" in result.category_counts
    assert result.artifact_ref is not None

    # Verify that the retrieved artifact content has masked tokens
    content = art_mgr.read_artifact_bytes(
        result.artifact_ref, result.document_id, result.release_allowed
    ).decode("utf-8")
    assert "<REDACTED_EMAIL>" in content
    assert "example.com" not in content


def test_orchestration_blocked_when_verification_fails(tmp_path):
    """Document must be BLOCKED and artifact access disabled if verification fails."""
    doc_path = DEMO_DIR / "01_synthetic_email.txt"
    trail = AuditTrail()
    art_mgr = ArtifactManager(storage_dir=tmp_path / "artifacts")

    result = process_document(
        str(doc_path),
        options={"simulate_verification_failure": True},
        audit_trail=trail,
        artifact_manager=art_mgr,
    )

    assert result.workflow_status == "blocked"
    assert result.current_stage == PipelineStage.BLOCKED
    assert result.verification_status == "FAIL"
    assert result.release_allowed is False
    assert result.artifact_ref is None
    assert "release is blocked" in (result.safe_error or "").lower()

    # Verify audit trail recorded blocked state
    events = trail.get_events(result.document_id)
    release_events = [e for e in events if e.event_type == "RELEASE_DECIDED"]
    assert len(release_events) == 1
    assert release_events[0].release_decision is False
    assert release_events[0].status == "blocked"


def test_orchestration_nonexistent_file():
    """Missing file immediately resolves to FAILED without unhandled exception."""
    result = process_document("nonexistent_demo_file_9999.txt")
    assert result.workflow_status == "failed"
    assert result.current_stage == PipelineStage.FAILED
    assert result.release_allowed is False
    assert result.safe_error_code == "ERR_FILE_NOT_FOUND"


def test_orchestration_empty_file_fail_closed():
    """Empty 0-byte file fails closed in ingestion stage."""
    doc_path = DEMO_DIR / "08_empty_document.txt"
    result = process_document(str(doc_path))
    assert result.workflow_status == "failed"
    assert result.current_stage == PipelineStage.FAILED
    assert result.release_allowed is False


def test_orchestration_independent_sessions_isolation(tmp_path):
    """Two concurrent document processing sessions do not cross-contaminate state."""
    trail = AuditTrail()
    art_mgr = ArtifactManager(storage_dir=tmp_path / "artifacts")

    res1 = process_document(
        str(DEMO_DIR / "01_synthetic_email.txt"),
        audit_trail=trail,
        artifact_manager=art_mgr,
    )
    res2 = process_document(
        str(DEMO_DIR / "04_clean_no_pii.txt"),
        audit_trail=trail,
        artifact_manager=art_mgr,
    )

    assert res1.document_id != res2.document_id
    assert res1.artifact_ref != res2.artifact_ref

    events1 = trail.get_events(res1.document_id)
    events2 = trail.get_events(res2.document_id)
    assert len(events1) > 0
    assert len(events2) > 0
    assert set(e.event_id for e in events1).isdisjoint(set(e.event_id for e in events2))
