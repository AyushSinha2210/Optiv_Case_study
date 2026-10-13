"""Deterministic, offset-safe text redaction and verification engine.

Owned by Member 3 (Yash) with integration interfaces for Member 5 (Tirth).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Iterable, List, Mapping, Optional

from .policy import PolicyError, get_replacement

if TYPE_CHECKING:
    from ..ingestion.schemas import ExtractedDocument
    from ..orchestration.artifacts import ArtifactManager
    from ..orchestration.models import DetectionResult, RedactionResult


class RedactionError(ValueError):
    """Raised when redaction input is unsafe or malformed."""


@dataclass(frozen=True)
class ValidatedSpan:
    entity_type: str
    start: int
    end: int
    replacement: str
    confidence: float | None = None


@dataclass(frozen=True)
class RedactionApplication:
    text: str
    spans: tuple[ValidatedSpan, ...]
    low_confidence_count: int


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_confidence(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RedactionError("Detection confidence must be numeric")
    confidence = float(value)
    if not 0.0 <= confidence <= 1.0:
        raise RedactionError("Detection confidence is outside the valid range")
    return confidence


def validate_spans(text: str, entities: Iterable[Mapping[str, Any]]) -> tuple[ValidatedSpan, ...]:
    """Validate offsets and reject overlap until the team defines precedence."""

    if not isinstance(text, str):
        raise RedactionError("Document text must be a string")
    if entities is None or isinstance(entities, (str, bytes)):
        raise RedactionError("Detection entities must be iterable")
    try:
        iterator = iter(entities)
    except TypeError as exc:
        raise RedactionError("Detection entities must be iterable") from exc

    validated: list[ValidatedSpan] = []
    for entity in iterator:
        if not isinstance(entity, Mapping):
            raise RedactionError("Each detection must be an object")
        entity_type = entity.get("type")
        start = entity.get("start")
        end = entity.get("end")
        confidence = _validate_confidence(entity.get("confidence"))
        if not _is_integer(start) or not _is_integer(end):
            raise RedactionError("Entity offsets must be integers")
        if start < 0 or end <= start or end > len(text):
            raise RedactionError("Entity offsets are outside the document")
        try:
            replacement = get_replacement(entity_type)
        except (PolicyError, AttributeError) as exc:
            raise RedactionError("Unsupported PII category") from exc
        validated.append(ValidatedSpan(entity_type.upper(), start, end, replacement, confidence))

    ordered = sorted(validated, key=lambda span: (span.start, span.end))
    for previous, current in zip(ordered, ordered[1:]):
        if current.start < previous.end:
            raise RedactionError("Overlapping PII spans require explicit resolution")
    return tuple(ordered)


def apply_redactions(
    text: str,
    entities: Iterable[Mapping[str, Any]],
    *,
    low_confidence_threshold: float = 0.50,
) -> RedactionApplication:
    """Replace from highest offset to lowest so offsets never become stale."""

    if not 0.0 <= low_confidence_threshold <= 1.0:
        raise RedactionError("Low-confidence threshold is invalid")
    spans = validate_spans(text, entities)
    result = text
    for span in sorted(spans, key=lambda item: item.start, reverse=True):
        result = result[: span.start] + span.replacement + result[span.end :]
    low_confidence_count = sum(
        span.confidence is not None and span.confidence < low_confidence_threshold
        for span in spans
    )
    return RedactionApplication(result, spans, low_confidence_count)


def redact_text(text: str, entities: Iterable[Mapping[str, Any]]) -> str:
    """Compatibility helper returning only the redacted string."""

    return apply_redactions(text, entities).text


class Redactor:
    """Applies entity masking and executes post-redaction verification."""

    def __init__(
        self,
        artifact_manager: Optional[Any] = None,
        verifier_detector: Optional[Callable[[Any], Any]] = None,
    ):
        if artifact_manager is None:
            from ..orchestration.artifacts import get_default_artifact_manager
            self.artifact_manager = get_default_artifact_manager()
        else:
            self.artifact_manager = artifact_manager
        self.verifier_detector = verifier_detector

    def redact_and_validate(
        self,
        doc: Any,
        detection: Any,
        simulate_verification_failure: bool = False,
    ) -> Any:
        """Mask detected PII, verify resulting artifact, and generate Contract C result."""
        from ..orchestration.models import FindingInfo, RedactionResult

        text = doc.text
        findings: List[FindingInfo] = []

        # Sort entities by start offset descending so earlier offsets remain valid during replacement
        entities_list = getattr(detection, "entities", [])
        sorted_entities = sorted(entities_list, key=lambda e: e.start, reverse=True)

        redacted_text = text
        applied_count = 0

        for ent in sorted_entities:
            # Ensure span bounds are valid within current string length
            if 0 <= ent.start < ent.end <= len(redacted_text):
                token = f"<REDACTED_{ent.type.upper()}>"
                redacted_text = redacted_text[:ent.start] + token + redacted_text[ent.end:]
                applied_count += 1
            else:
                findings.append(
                    FindingInfo(
                        code="WARN_INVALID_SPAN_BOUNDS",
                        message="Entity offset out of document boundary during redaction",
                        category=ent.type,
                    )
                )

        # Step 2: Independent Verification Re-scan
        verification_status = "PASS"
        release_allowed = True

        if simulate_verification_failure:
            verification_status = "FAIL"
            release_allowed = False
            findings.append(
                FindingInfo(
                    code="ERR_LEAKAGE_DETECTED",
                    message="Simulated leakage trigger detected residual PII in artifact",
                )
            )
        elif self.verifier_detector is not None:
            try:
                # Wrap redacted text into a temporary document contract for re-scan
                from ..ingestion.schemas import ExtractedDocument
                verify_doc = ExtractedDocument(
                    document_id=f"verify-{doc.document_id}",
                    source_type=doc.source_type,
                    text=redacted_text,
                    pages=[],
                    warnings=[],
                    extraction_status="success",
                )
                re_scan_res = self.verifier_detector(verify_doc)
                if re_scan_res.entities:
                    verification_status = "FAIL"
                    release_allowed = False
                    findings.append(
                        FindingInfo(
                            code="ERR_RESIDUAL_PII_LEAKAGE",
                            message=f"Post-redaction re-scan detected {len(re_scan_res.entities)} residual entities",
                        )
                    )
            except Exception:
                verification_status = "INCOMPLETE"
                release_allowed = False
                findings.append(
                    FindingInfo(
                        code="ERR_VERIFICATION_INTERRUPTED",
                        message="Verification re-scan encountered an internal exception",
                    )
                )

        # Step 3: Persist redacted artifact in managed sandbox
        artifact_ref = self.artifact_manager.store_artifact(
            document_id=doc.document_id,
            content=redacted_text,
            file_extension=doc.source_type if doc.source_type in ("txt", "docx") else "txt",
            content_type="text/plain",
        )

        return RedactionResult(
            document_id=doc.document_id,
            artifact_ref=artifact_ref,
            redactions_applied=applied_count,
            verification_status=verification_status,
            release_allowed=release_allowed,
            findings=findings,
        )


def redact_and_validate(
    doc: Any,
    detection: Any,
    artifact_manager: Optional[Any] = None,
    simulate_verification_failure: bool = False,
    **kwargs: Any,
) -> Any:
    """Public functional interface for redaction and verification."""
    from ..detection.detector import detect_pii
    redactor = Redactor(artifact_manager=artifact_manager, verifier_detector=detect_pii)
    return redactor.redact_and_validate(
        doc, detection, simulate_verification_failure=simulate_verification_failure
    )
