"""Public entry point: detect_pii(document) -> DetectionResult (Contract B).

Fail-closed: a failed extraction raises DetectionInputError rather than
returning an empty result, because "no entities" would look like "safe".
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .classifier import resolve_overlaps
from .ner_detector import NerBackend, detect_ner
from .pattern_detector import detect_patterns
from .schemas import DetectedEntity, DetectionInputError, DetectionResult, DetectionWarning

if TYPE_CHECKING:  # type-only; avoids a runtime dependency on the ingestion package
    from ..ingestion.schemas import ExtractedDocument


def _warn(code: str, message: str) -> DetectionWarning:
    return DetectionWarning(code=code, message=message)


def detect_pii(
    document: "ExtractedDocument",
    ner_backend: Optional[NerBackend] = None,
    options: Optional[dict[str, Any]] = None,
    **kwargs: Any,
) -> DetectionResult:
    """Classify PII spans in `document.text`.

    Args:
        document: any object with document_id, text and extraction_status
            (an ExtractedDocument from Member 1, or a compatible stand-in).
        ner_backend: optional `text -> [(label, start, end, score)]` callable.
            None disables PERSON detection and adds a NER_UNAVAILABLE warning.
        options: optional configuration dictionary.

    Raises:
        DetectionInputError: if the document is malformed or extraction failed.
    """
    document_id = getattr(document, "document_id", None)
    text = getattr(document, "text", None)
    status = getattr(document, "extraction_status", None)

    if not isinstance(document_id, str) or not document_id:
        raise DetectionInputError("document_id is required")
    if not isinstance(text, str):
        raise DetectionInputError("text must be a string")
    if status == "failed":
        raise DetectionInputError("upstream extraction failed; detection refused (fail-closed)")
    if status not in ("success", "partial"):
        raise DetectionInputError("unknown extraction_status")

    warnings: list[DetectionWarning] = []
    if status == "partial":
        warnings.append(
            _warn("UPSTREAM_PARTIAL_EXTRACTION", "Extraction was partial; coverage may be incomplete.")
        )

    if not text.strip():
        warnings.append(_warn("EMPTY_TEXT", "No text to scan."))
        return DetectionResult(document_id=document_id, entities=[], warnings=warnings)

    pattern_candidates = detect_patterns(text)
    ner_candidates, ner_warnings = detect_ner(text, ner_backend)
    warnings.extend(ner_warnings)

    valid = []
    invalid = 0
    for candidate in pattern_candidates + ner_candidates:
        in_bounds = 0 <= candidate.start < candidate.end <= len(text)
        if in_bounds and "\f" not in text[candidate.start:candidate.end]:
            valid.append(candidate)
        else:
            invalid += 1
    if invalid:
        warnings.append(_warn("INVALID_SPAN_DROPPED", f"{invalid} candidate span(s) dropped as invalid."))

    resolved, dropped = resolve_overlaps(valid)
    if dropped:
        warnings.append(_warn("OVERLAP_RESOLVED", f"{dropped} overlapping candidate(s) resolved by precedence."))

    confidence_threshold = 0.0
    if options and "confidence_threshold" in options:
        confidence_threshold = float(options["confidence_threshold"])

    entities = [
        DetectedEntity(
            type=c.type,
            start=c.start,
            end=c.end,
            confidence=round(c.confidence, 4),
        )
        for c in resolved
        if c.confidence >= confidence_threshold
    ]
    return DetectionResult(document_id=document_id, entities=entities, warnings=warnings)


class PIIDetector:
    """Deterministic pattern and contextual PII detector wrapper conforming to Contract B."""

    def __init__(
        self,
        confidence_threshold: float = 0.5,
        ner_backend: Optional[NerBackend] = None,
        use_default_ner: bool = True,
    ) -> None:
        self.confidence_threshold = confidence_threshold
        if ner_backend is None and use_default_ner:
            from .ner_detector import get_default_ner_backend
            self.ner_backend = get_default_ner_backend()
        else:
            self.ner_backend = ner_backend


    def detect(self, doc: "ExtractedDocument", options: Optional[dict[str, Any]] = None) -> DetectionResult:
        """Scan ExtractedDocument.text and return Contract B DetectionResult."""
        opts = dict(options or {})
        if "confidence_threshold" not in opts:
            opts["confidence_threshold"] = self.confidence_threshold
        return detect_pii(doc, ner_backend=self.ner_backend, options=opts)
