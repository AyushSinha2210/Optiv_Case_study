from types import SimpleNamespace

from src.pii_guard.orchestration import pipeline


def test_partial_extraction_is_blocked_before_redaction(tmp_path, monkeypatch):
    source = tmp_path / "partial.txt"
    source.write_text("possibly incomplete sensitive document", encoding="utf-8")

    extracted = SimpleNamespace(
        document_id="doc-partial-test",
        extraction_status="partial",
        warnings=[SimpleNamespace(code="WARN_OCR_LOW_CONFIDENCE")],
        source_type="txt",
        pages=[],
        text="possibly incomplete sensitive document",
    )

    monkeypatch.setattr(pipeline, "extract_document", lambda *_args, **_kwargs: extracted)
    result = pipeline.process_document(str(source))

    assert result.workflow_status == "incomplete"
    assert result.current_stage.value == "INCOMPLETE"
    assert result.extraction_status == "partial"
    assert result.release_allowed is False
    assert result.artifact_ref is None
    assert "WARN_PARTIAL_EXTRACTION_REQUIRES_REVIEW" in result.safe_warnings


def test_audit_details_scrub_sensitive_values():
    from src.cadence_tprm.services.audit_service import sanitize_audit_details

    sanitized = sanitize_audit_details({
        "contract_reference": "IC-123",
        "payload": {"email": "person@example.test", "secret": "do-not-store"},
        "event_type": "contract.executed",
    })

    assert sanitized["contract_reference"] == "IC-123"
    assert "payload" not in sanitized
    assert sanitized["event_type"] == "contract.executed"
