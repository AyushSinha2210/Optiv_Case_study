"""Security leakage regression tests using unique synthetic canary tokens.

PRIVACY VERIFICATION:
Proves that sensitive personal identifiers and canary tokens NEVER appear in:
1. Audit records and serialized audit logs.
2. Machine-readable JSON reports (Contract D).
3. Human-readable executive summaries.
4. CSV telemetry exports.
5. Public ProcessingResult data structures.
6. Public error messages and log outputs.
7. Fixture manifests.
"""

import json
import logging
from pathlib import Path
import pytest

from src.pii_guard.orchestration.pipeline import process_document
from src.pii_guard.reporting.audit import AuditTrail
from src.pii_guard.reporting.report_generator import generate_report, generate_human_readable_summary
from src.pii_guard.reporting.export import export_to_json, export_to_csv

CANARY_PERSON = "SYNTHETIC_PERSON_CANARY_84721"
CANARY_EMAIL = "canary.victim.58319@example.com"
CANARY_PHONE = "(555) 019-27463"
CANARY_GOV_ID = "000-88-27463"

ALL_CANARIES = [CANARY_PERSON, CANARY_EMAIL, CANARY_PHONE, CANARY_GOV_ID]


@pytest.fixture
def canary_test_file(tmp_path):
    """Create a temporary test document embedded with distinct canary markers."""
    doc_path = tmp_path / "canary_payload.txt"
    content = (
        f"Cadence Financial Advisory Audit\n\n"
        f"Client Contact: {CANARY_PERSON}\n"
        f"Notification Address: {CANARY_EMAIL}\n"
        f"Emergency Callback: {CANARY_PHONE}\n"
        f"Synthetic Identification: {CANARY_GOV_ID}\n\n"
        f"This document is used strictly to verify privacy leakage barriers.\n"
    )
    doc_path.write_text(content, encoding="utf-8")
    return str(doc_path)


def test_zero_canary_leakage_in_all_metadata_outputs(canary_test_file, caplog):
    """Run full pipeline and prove 0 canary tokens leak across any reporting or audit artifact."""
    trail = AuditTrail()

    with caplog.at_level(logging.DEBUG):
        result = process_document(canary_test_file, audit_trail=trail)

    # 1. Inspect public ProcessingResult dictionary
    safe_result_dict = result.to_safe_dict()
    result_str = json.dumps(safe_result_dict)
    for canary in ALL_CANARIES:
        assert canary not in result_str, f"Canary {canary} leaked in ProcessingResult.to_safe_dict()"

    # 2. Inspect Audit Trail records
    audit_events = trail.export_sanitized_log(result.document_id)
    audit_str = json.dumps(audit_events)
    for canary in ALL_CANARIES:
        assert canary not in audit_str, f"Canary {canary} leaked in AuditTrail.export_sanitized_log()"

    # 3. Inspect Contract D JSON Report
    report = generate_report(result)
    report_json = export_to_json(report)
    for canary in ALL_CANARIES:
        assert canary not in report_json, f"Canary {canary} leaked in export_to_json()"

    # 4. Inspect Human-Readable Summary
    summary = generate_human_readable_summary(report)
    for canary in ALL_CANARIES:
        assert canary not in summary, f"Canary {canary} leaked in generate_human_readable_summary()"

    # 5. Inspect CSV Export
    csv_out = export_to_csv([report])
    for canary in ALL_CANARIES:
        assert canary not in csv_out, f"Canary {canary} leaked in export_to_csv()"

    # 6. Inspect Captured Logs
    log_text = caplog.text
    for canary in ALL_CANARIES:
        assert canary not in log_text, f"Canary {canary} leaked in application logs!"


def test_manifest_file_zero_canary_leakage():
    """Verify that demo_samples/manifest.json contains strictly metadata and no canary values."""
    manifest_path = Path(__file__).resolve().parent.parent.parent / "demo_samples" / "manifest.json"
    assert manifest_path.is_file()
    content = manifest_path.read_text(encoding="utf-8")
    data = json.loads(content)

    for canary in ALL_CANARIES:
        assert canary not in content

    # Confirm manifest entries do not contain raw document text
    for fix in data["fixtures"]:
        assert "text" not in fix
        assert "content" not in fix
        assert "raw" not in fix
