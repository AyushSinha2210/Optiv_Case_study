"""Security regression test suite proving fail-closed release gate invariants.

CRITICAL INVARIANTS TESTED:
A document is released ONLY when:
    verification_status == "PASS" AND release_allowed is True
All other combinations MUST fail closed, blocking artifact download and setting release_allowed = False.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from src.pii_guard.orchestration.pipeline import process_document
from src.pii_guard.orchestration.models import (
    RedactionResult,
    DetectionResult,
    FindingInfo,
)
from src.pii_guard.orchestration.state import PipelineStage
from src.pii_guard.orchestration.artifacts import ArtifactManager
from src.pii_guard.orchestration.errors import ArtifactAccessError
from src.pii_guard.reporting.audit import AuditTrail

DEMO_DIR = Path(__file__).resolve().parent.parent.parent / "demo_samples" / "fixtures"


@pytest.fixture
def clean_doc_path():
    return str(DEMO_DIR / "04_clean_no_pii.txt")


def test_release_blocked_when_verification_status_is_fail(clean_doc_path, tmp_path):
    """verification_status == 'FAIL' must force release_allowed=False and block artifact access."""
    art_mgr = ArtifactManager(storage_dir=tmp_path)
    
    def mock_redactor(doc, det):
        token = art_mgr.store_artifact(doc.document_id, "Masked text with residual issue")
        return RedactionResult(
            document_id=doc.document_id,
            artifact_ref=token,
            redactions_applied=1,
            verification_status="FAIL",
            release_allowed=True,  # Conflicting flag: verifier says FAIL
            findings=[FindingInfo(code="ERR_RESIDUAL_PII", message="Residual PII detected")],
        )

    res = process_document(clean_doc_path, redactor_fn=mock_redactor, artifact_manager=art_mgr)
    assert res.release_allowed is False
    assert res.workflow_status == "blocked"
    assert res.current_stage == PipelineStage.BLOCKED
    assert res.artifact_ref is None


def test_release_blocked_when_verification_status_is_incomplete(clean_doc_path, tmp_path):
    """verification_status == 'INCOMPLETE' must withhold release."""
    art_mgr = ArtifactManager(storage_dir=tmp_path)

    def mock_redactor(doc, det):
        token = art_mgr.store_artifact(doc.document_id, "Incomplete verification text")
        return RedactionResult(
            document_id=doc.document_id,
            artifact_ref=token,
            redactions_applied=1,
            verification_status="INCOMPLETE",
            release_allowed=True,
        )

    res = process_document(clean_doc_path, redactor_fn=mock_redactor, artifact_manager=art_mgr)
    assert res.release_allowed is False
    assert res.workflow_status == "incomplete"
    assert res.current_stage == PipelineStage.INCOMPLETE
    assert res.artifact_ref is None


def test_release_blocked_when_release_allowed_flag_is_false_even_if_pass(clean_doc_path, tmp_path):
    """Even if verification_status == 'PASS', release_allowed=False must block release."""
    art_mgr = ArtifactManager(storage_dir=tmp_path)

    def mock_redactor(doc, det):
        token = art_mgr.store_artifact(doc.document_id, "Verified clean text")
        return RedactionResult(
            document_id=doc.document_id,
            artifact_ref=token,
            redactions_applied=1,
            verification_status="PASS",
            release_allowed=False,  # Explicit policy override forbidding release
        )

    res = process_document(clean_doc_path, redactor_fn=mock_redactor, artifact_manager=art_mgr)
    assert res.release_allowed is False
    assert res.workflow_status in ("blocked", "incomplete")
    assert res.artifact_ref is None


def test_release_blocked_when_verifier_throws_exception(clean_doc_path, tmp_path):
    """Exceptions raised during redaction/verification must fail closed."""
    def exploding_redactor(doc, det):
        raise RuntimeError("Crash during model verification inference")

    res = process_document(clean_doc_path, redactor_fn=exploding_redactor)
    assert res.release_allowed is False
    assert res.workflow_status == "failed"
    assert res.current_stage == PipelineStage.FAILED
    assert res.artifact_ref is None
    assert "Crash during model verification" not in (res.safe_error or "")


def test_release_blocked_when_earlier_stage_failed(tmp_path):
    """If extraction fails, later stages never run and release is impossible."""
    res = process_document("nonexistent_file_to_fail.txt")
    assert res.release_allowed is False
    assert res.workflow_status == "failed"
    assert res.current_stage == PipelineStage.FAILED
    assert res.artifact_ref is None


def test_reports_cannot_grant_artifact_access(clean_doc_path, tmp_path):
    """Having a valid report or audit ID does not permit bypassing artifact security checks."""
    art_mgr = ArtifactManager(storage_dir=tmp_path)
    res = process_document(
        clean_doc_path,
        options={"simulate_verification_failure": True},
        artifact_manager=art_mgr,
    )

    # Confirm document was blocked
    assert res.workflow_status == "blocked"
    assert res.release_allowed is False
    assert res.report_id is not None  # Report was generated

    # Attempt to retrieve artifact using report ID
    with pytest.raises(ArtifactAccessError):
        art_mgr.validate_and_resolve_path(
            artifact_ref=res.report_id,
            authorized_document_id=res.document_id,
            release_allowed=res.release_allowed,
        )
