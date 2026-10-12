"""Deterministic, offset-safe text redaction."""

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .policy import PolicyError, get_replacement


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
