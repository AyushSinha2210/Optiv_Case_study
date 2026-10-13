"""Stable public facade used by Member 5's orchestrator."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .gate import evaluate_release
from .redactor import RedactionError, apply_redactions
from .schemas import RedactionFinding, RedactionResult
from .verifier import calculate_structure_score, verify_redacted_text, verify_saved_artifact


def _as_mapping(value: Any) -> Mapping[str, Any]:
    """Accept repository Pydantic models and plain dictionaries."""

    if isinstance(value, Mapping):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump()
        if isinstance(dumped, Mapping):
            return dumped
    raise TypeError("Expected a mapping or Pydantic model")


def _safe_result(document_id: Any, status: str, check: str) -> RedactionResult:
    verification_status = "FAIL" if status == "FAIL" else "INCOMPLETE"
    return RedactionResult(
        document_id=document_id if isinstance(document_id, str) else "unknown",
        artifact_ref=None,
        redactions_applied=0,
        verification_status=verification_status,
        release_allowed=False,
        findings=[RedactionFinding(check=check)],
    )


def redact_and_validate(
    document: Any,
    detection_result: Any,
    *,
    artifact_ref: str | None = None,
    artifact_text_reader: Callable[[Any], str] | None = None,
    artifact_manager: Any | None = None,
    minimum_structure_score: float = 0.80,
    simulate_verification_failure: bool = False,
    **kwargs: Any,
) -> RedactionResult:
    """Redact, verify, and return Contract C with fail-closed release behavior.

    ``artifact_text_reader`` must reopen the actual saved output. Omitting it
    intentionally produces INCOMPLETE and prevents release.

    If ``artifact_manager`` is provided, the redacted content is persisted in the
    managed sandbox and automatically validated via the artifact reader.
    """

    document_id = getattr(document, "document_id", None)
    try:
        doc = _as_mapping(document)
        detection = _as_mapping(detection_result)
    except TypeError:
        return _safe_result(document_id, "INCOMPLETE", "INVALID_INPUT_SCHEMA")

    document_id = doc.get("document_id")
    if not isinstance(document_id, str) or not document_id:
        return _safe_result(document_id, "INCOMPLETE", "INVALID_DOCUMENT_ID")
    if detection.get("document_id") != document_id:
        return _safe_result(document_id, "INCOMPLETE", "DOCUMENT_ID_MISMATCH")
    if doc.get("extraction_status") != "success":
        return _safe_result(document_id, "INCOMPLETE", "EXTRACTION_NOT_COMPLETE")
    if not isinstance(doc.get("text"), str):
        return _safe_result(document_id, "INCOMPLETE", "DOCUMENT_TEXT_MISSING")
    if not 0.0 <= minimum_structure_score <= 1.0:
        return _safe_result(document_id, "INCOMPLETE", "INVALID_STRUCTURE_THRESHOLD")

    entities = detection.get("entities")
    if not isinstance(entities, list):
        return _safe_result(document_id, "INCOMPLETE", "INVALID_DETECTION_RESULT")

    original_text = doc["text"]
    try:
        application = apply_redactions(original_text, entities)
    except RedactionError:
        return _safe_result(document_id, "FAIL", "INVALID_REDACTION_INPUT")

    # If an ArtifactManager is provided, persist the artifact in the sandbox
    if artifact_manager is not None:
        source_type = doc.get("source_type", "txt")
        file_ext = source_type if source_type in ("txt", "docx") else "txt"
        stored_ref = artifact_manager.store_artifact(
            document_id=document_id,
            content=application.text,
            file_extension=file_ext,
            content_type="text/plain",
        )
        artifact_ref = stored_ref
        artifact_text_reader = lambda ref: artifact_manager.read_artifact_bytes(
            ref, document_id, True
        ).decode("utf-8")

    text_check = verify_redacted_text(original_text, application.text, entities)

    if simulate_verification_failure:
        artifact_check = {
            "status": "FAIL",
            "findings": [{"check": "simulated_verification_failure"}],
        }
    else:
        artifact_check = verify_saved_artifact(
            artifact_ref, artifact_text_reader, original_text, entities
        )

    structure_score = calculate_structure_score(original_text, application.text)
    structure_status = "PASS" if structure_score >= minimum_structure_score else "FAIL"
    gate = evaluate_release(
        redaction_succeeded=True,
        text_verification_status=text_check["status"],
        artifact_verification_status=artifact_check["status"],
        structure_status=structure_status,
    )

    raw_findings = [
        *text_check["findings"],
        *artifact_check["findings"],
        *([] if structure_status == "PASS" else [{"check": "structure_score_below_threshold"}]),
    ]
    if application.low_confidence_count:
        raw_findings.append({
            "check": "low_confidence_entities_redacted_conservatively",
            "count": application.low_confidence_count,
        })
    findings = [RedactionFinding.model_validate(item) for item in raw_findings]
    verification_status = (
        "PASS"
        if gate["status"] == "PASS"
        else "FAIL"
        if text_check["status"] == "FAIL"
        or artifact_check["status"] == "FAIL"
        or structure_status == "FAIL"
        else "INCOMPLETE"
    )
    return RedactionResult(
        document_id=document_id,
        artifact_ref=artifact_ref if gate["release_allowed"] else None,
        redactions_applied=len(application.spans),
        verification_status=verification_status,
        release_allowed=bool(gate["release_allowed"]),
        findings=findings,
    )
