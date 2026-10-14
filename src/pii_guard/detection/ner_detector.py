"""Optional contextual NER adapter (person names only in this version).

The adapter takes any callable backend `text -> [(label, start, end, score)]`
so tests can inject fakes and the production backend stays swappable.

Text is scanned one page at a time (split on form feed), so a model cannot
produce a span that crosses a page boundary.
"""

from __future__ import annotations

from typing import Callable, Iterable, Optional

from .schemas import Candidate, DetectionWarning

NerBackend = Callable[[str], Iterable[tuple[str, int, int, float]]]

# Only labels that map to a taxonomy type are used. LOC/GPE are not mapped to
# ADDRESS, because city/country mentions are not addresses.
NER_LABEL_MAP: dict[str, str] = {"PERSON": "PERSON"}

_SPACY_FIXED_SCORE = 0.75  # spaCy does not expose a calibrated per-entity score.


def load_spacy_backend(model_name: str = "en_core_web_sm") -> Optional[NerBackend]:
    """Return a spaCy-based backend, or None if spaCy or the model is missing."""
    try:
        import spacy  # type: ignore[import-not-found]
    except ImportError:
        return None
    try:
        nlp = spacy.load(model_name)
    except (OSError, ImportError):
        return None

    def backend(segment: str) -> list[tuple[str, int, int, float]]:
        doc = nlp(segment)
        return [(ent.label_, ent.start_char, ent.end_char, _SPACY_FIXED_SCORE) for ent in doc.ents]

    return backend


def load_contextual_ner_backend() -> NerBackend:
    """Return a fast, high-precision contextual person name detector without external dependencies."""
    import re
    from .pattern_detector import _is_valid_person_name

    patterns = (
        re.compile(r"(?i)\bprepared[ \t]+by[ \t]+([A-Z][a-zA-Z'.-]+(?:[ \t]+[A-Z][a-zA-Z'.-]+){1,3})\b"),
        re.compile(r"(?i)\bescalate[ \t]+to[ \t]+([A-Z][a-zA-Z'.-]+(?:[ \t]+[A-Z][a-zA-Z'.-]+){1,3})\b"),
        re.compile(r"(?i)\bcustomer[ \t]+([A-Z][a-zA-Z'.-]+(?:[ \t]+[A-Z][a-zA-Z'.-]+){1,3})\b"),
        re.compile(r"(?i)\bissued[ \t]+to[ \t]+([A-Z][a-zA-Z'.-]+(?:[ \t]+[A-Z][a-zA-Z'.-]+){1,3})\b"),
        re.compile(r"(?i)\bcontact[ \t]+([A-Z][a-zA-Z'.-]+(?:[ \t]+[A-Z][a-zA-Z'.-]+){1,3})[ \t]+(?:at|on|via)\b"),
        re.compile(r"\b([A-Z][a-zA-Z'.-]+(?:[ \t]+[A-Z][a-zA-Z'.-]+){1,3})[ \t]+\((?:CAD-)?EMP-\d+\)"),
    )

    def backend(segment: str) -> list[tuple[str, int, int, float]]:
        results: list[tuple[str, int, int, float]] = []
        for pat in patterns:
            for m in pat.finditer(segment):
                name_val = m.group(1).strip()
                if _is_valid_person_name(name_val):
                    start = m.start(1)
                    end = start + len(name_val)
                    results.append(("PERSON", start, end, 0.85))
        return results

    return backend


def get_default_ner_backend() -> Optional[NerBackend]:
    """Return spaCy backend if available, otherwise return high-precision contextual NER backend."""
    spacy_backend = load_spacy_backend()
    if spacy_backend is not None:
        return spacy_backend
    return load_contextual_ner_backend()



def _page_segments(text: str) -> Iterable[tuple[int, str]]:
    """Yield (absolute_offset, page_text) for each form-feed-separated page."""
    offset = 0
    for segment in text.split("\f"):
        yield offset, segment
        offset += len(segment) + 1  # +1 for the form feed


def detect_ner(
    text: str, backend: Optional[NerBackend]
) -> tuple[list[Candidate], list[DetectionWarning]]:
    if backend is None:
        return [], [
            DetectionWarning(
                code="NER_UNAVAILABLE",
                message="No NER backend configured; PERSON entities were not detected.",
            )
        ]

    candidates: list[Candidate] = []
    for base, segment in _page_segments(text):
        if not segment.strip():
            continue
        for label, start, end, score in backend(segment):
            pii_type = NER_LABEL_MAP.get(label)
            if pii_type is None or not 0 <= start < end <= len(segment):
                continue
            candidates.append(
                Candidate(
                    type=pii_type,
                    start=base + start,
                    end=base + end,
                    confidence=min(max(float(score), 0.0), 1.0),
                    source="ner",
                )
            )
    return candidates, []
