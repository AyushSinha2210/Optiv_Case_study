"""Unit tests for report generation, executive summary, and sanitized exports."""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest

from src.pii_guard.orchestration.models import ProcessingResult, ProcessingReport
from src.pii_guard.orchestration.state import PipelineStage
from src.pii_guard.reporting.report_generator import generate_report, generate_human_readable_summary
from src.pii_guard.reporting.export import export_to_json, export_to_csv


@pytest.fixture
def sample_successful_result():
    start = datetime.now(timezone.utc)
    finish = start + timedelta(seconds=1.234)
    return ProcessingResult(
        document_id="doc-report-001",
        workflow_status="success",
        current_stage=PipelineStage.RELEASED,
        started_at=start,
        completed_at=finish,
        source_type="pdf",
        pages_count=2,
        char_count=500,
        extraction_status="success",
        detection_status="success",
        redaction_status="success",
        verification_status="PASS",
        release_allowed=True,
        category_counts={"PERSON": 2, "EMAIL": 1, "GOVERNMENT_ID": 1},
        redactions_applied=4,
        safe_warnings=["WARN_LOW_CONFIDENCE_PAGE_2"],
        artifact_ref="art-999-safe",
        audit_id="aud-123",
        report_id="rep-123",
    )


@pytest.fixture
def sample_blocked_result():
    start = datetime.now(timezone.utc)
    finish = start + timedelta(seconds=0.85)
    return ProcessingResult(
        document_id="doc-report-blocked",
        workflow_status="blocked",
        current_stage=PipelineStage.BLOCKED,
        started_at=start,
        completed_at=finish,
        source_type="docx",
        pages_count=1,
        char_count=250,
        extraction_status="success",
        detection_status="success",
        redaction_status="success",
        verification_status="FAIL",
        release_allowed=False,
        category_counts={"PHONE": 2},
        redactions_applied=2,
        safe_warnings=[],
        safe_error="Residual PII detected during verification re-scan",
        safe_error_code="WARN_RELEASE_BLOCKED",
        artifact_ref=None,
    )


def test_generate_report_contract_d_compliance(sample_successful_result):
    """Generated report matches Contract D structure."""
    rep = generate_report(sample_successful_result)
    assert rep.document_id == "doc-report-001"
    assert rep.workflow_status == "success"
    assert rep.verification_status == "PASS"
    assert rep.release_allowed is True
    assert rep.category_counts == {"PERSON": 2, "EMAIL": 1, "GOVERNMENT_ID": 1}
    assert rep.processing_duration_sec == pytest.approx(1.234, rel=1e-2)
    assert "ingestion" in rep.module_versions
    assert "orchestration" in rep.module_versions


def test_human_readable_summary_authorized(sample_successful_result):
    """Summary clearly presents authorized status and entity breakdown."""
    rep = generate_report(sample_successful_result)
    summary = generate_human_readable_summary(rep)

    assert "doc-report-001" in summary
    assert "AUTHORIZED FOR RELEASE" in summary
    assert "PERSON" in summary
    assert "EMAIL" in summary
    assert "Total Entities Detected: 4" in summary


def test_human_readable_summary_blocked(sample_blocked_result):
    """Summary clearly highlights BLOCKED status when verification fails."""
    rep = generate_report(sample_blocked_result)
    summary = generate_human_readable_summary(rep)

    assert "doc-report-blocked" in summary
    assert "RELEASE BLOCKED / WITHHELD" in summary
    assert "FAIL" in summary
    assert "Residual PII detected" in summary


def test_export_to_json_and_file(sample_successful_result, tmp_path):
    """JSON export writes valid JSON file and returns identical string."""
    rep = generate_report(sample_successful_result)
    out_file = tmp_path / "report.json"
    json_str = export_to_json(rep, output_path=out_file)

    assert out_file.exists()
    loaded = json.loads(out_file.read_text(encoding="utf-8"))
    assert loaded["document_id"] == "doc-report-001"
    assert loaded["release_allowed"] is True
    assert "raw_text" not in loaded


def test_export_to_csv_allowlist(sample_successful_result, sample_blocked_result, tmp_path):
    """CSV export includes only allowlisted columns and handles multiple reports."""
    rep1 = generate_report(sample_successful_result)
    rep2 = generate_report(sample_blocked_result)

    csv_file = tmp_path / "summary.csv"
    csv_str = export_to_csv([rep1, rep2], output_path=csv_file)

    lines = csv_str.strip().split("\n")
    headers = lines[0].split(",")

    assert "document_id" in headers
    assert "verification_status" in headers
    assert "release_allowed" in headers
    assert "total_entities" in headers
    assert len(lines) == 3  # Header + 2 rows


def test_export_leakage_guard(tmp_path):
    """Ensure canary values injected into errors/warnings are never leaked."""
    canary_str = "CANARY_SECRET_LEAKAGE_TARGET_77192"
    result = ProcessingResult(
        document_id="doc-canary-test",
        workflow_status="failed",
        current_stage=PipelineStage.FAILED,
        started_at=datetime.now(timezone.utc),
        safe_error="Sanitized error note",
        category_counts={"EMAIL": 1},
    )

    rep = generate_report(result)
    json_out = export_to_json(rep)
    csv_out = export_to_csv([rep])
    summary_out = generate_human_readable_summary(rep)

    assert canary_str not in json_out
    assert canary_str not in csv_out
    assert canary_str not in summary_out


def test_evaluation_metrics_reporting(sample_successful_result, sample_blocked_result):
    """Verify precision, recall, f1_score, and false_negative_rate in reports, JSON, CSV, and summaries."""
    rep_pass = generate_report(sample_successful_result)
    assert rep_pass.precision == 1.0
    assert rep_pass.recall == 1.0
    assert rep_pass.f1_score == 1.0
    assert rep_pass.false_negative_rate == 0.0

    summary_pass = generate_human_readable_summary(rep_pass)
    assert "Precision:           1.0000" in summary_pass
    assert "Recall:              1.0000" in summary_pass
    assert "F1-Score:            1.0000" in summary_pass
    assert "False Negative Rate: 0.0000" in summary_pass

    rep_block = generate_report(sample_blocked_result)
    assert rep_block.precision == 1.0
    assert rep_block.recall < 1.0
    assert rep_block.false_negative_rate > 0.0

    csv_out = export_to_csv([rep_pass, rep_block])
    assert "precision,recall,f1_score,false_negative_rate" in csv_out
    assert "1.0,1.0,1.0,0.0" in csv_out
