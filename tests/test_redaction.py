"""Member 3 unit and fail-closed integration tests."""

from pii_guard.detection.schemas import DetectedEntity, DetectionResult
from pii_guard.ingestion.schemas import ExtractedDocument
from pii_guard.redaction.redactor import RedactionError, redact_text
from pii_guard.redaction.service import redact_and_validate
from pii_guard.redaction.verifier import verify_redacted_text


def make_document(text: str) -> ExtractedDocument:
    return ExtractedDocument(
        document_id="doc-001",
        source_type="txt",
        text=text,
        pages=[],
        warnings=[],
        extraction_status="success",
    )


def make_detection(*entities: dict) -> DetectionResult:
    return DetectionResult(
        document_id="doc-001",
        entities=[DetectedEntity(**entity) for entity in entities],
    )


def test_multiple_spans_are_replaced_right_to_left():
    text = "Contact Alice at alice@example.com"
    result = redact_text(
        text,
        [
            {"type": "PERSON", "start": 8, "end": 13},
            {"type": "EMAIL", "start": 17, "end": 34},
        ],
    )
    assert result == "Contact [REDACTED_PERSON] at [REDACTED_EMAIL]"


def test_employee_id_has_a_contract_replacement():
    assert redact_text("ID EMP-42", [{"type": "EMPLOYEE_ID", "start": 3, "end": 9}]) == "ID [REDACTED_EMPLOYEE_ID]"


def test_invalid_span_is_rejected():
    try:
        redact_text("Email: a@example.com", [{"type": "EMAIL", "start": 7, "end": 100}])
    except RedactionError:
        pass
    else:
        raise AssertionError("out-of-range span was accepted")


def test_overlap_is_rejected():
    try:
        redact_text(
            "Alice alice@example.com",
            [
                {"type": "PERSON", "start": 0, "end": 5},
                {"type": "EMAIL", "start": 4, "end": 23},
            ],
        )
    except RedactionError:
        pass
    else:
        raise AssertionError("overlapping spans were accepted")


def test_unknown_category_is_rejected():
    try:
        redact_text("secret", [{"type": "UNKNOWN", "start": 0, "end": 6}])
    except RedactionError:
        pass
    else:
        raise AssertionError("unknown category was accepted")


def test_verifier_does_not_expose_sensitive_values():
    result = verify_redacted_text(
        "Email: alice@example.com",
        "Email: alice@example.com",
        [{"type": "EMAIL", "start": 7, "end": 24}],
    )
    assert result["status"] == "FAIL"
    assert "alice@example.com" not in repr(result)


def test_missing_artifact_check_blocks_release():
    result = redact_and_validate(
        make_document("Email: alice@example.com"),
        make_detection({"type": "EMAIL", "start": 7, "end": 24, "confidence": 0.99}),
    )
    assert result.verification_status == "INCOMPLETE"
    assert result.release_allowed is False


def test_reopened_clean_artifact_allows_release():
    result = redact_and_validate(
        make_document("Email: alice@example.com"),
        make_detection({"type": "EMAIL", "start": 7, "end": 24, "confidence": 0.99}),
        artifact_ref="private/synthetic-output.txt",
        artifact_text_reader=lambda _: "Email: [REDACTED_EMAIL]",
    )
    assert result.verification_status == "PASS"
    assert result.release_allowed is True
    assert result.artifact_ref == "private/synthetic-output.txt"


def test_leaking_saved_artifact_blocks_release():
    result = redact_and_validate(
        make_document("Email: alice@example.com"),
        make_detection({"type": "EMAIL", "start": 7, "end": 24, "confidence": 0.99}),
        artifact_ref="private/bad-output.txt",
        artifact_text_reader=lambda _: "Email: alice@example.com",
    )
    assert result.verification_status == "FAIL"
    assert result.release_allowed is False


def test_document_id_mismatch_blocks_release():
    detection = DetectionResult(document_id="doc-999", entities=[])
    result = redact_and_validate(make_document("No PII"), detection)
    assert result.release_allowed is False
    assert result.verification_status == "INCOMPLETE"
