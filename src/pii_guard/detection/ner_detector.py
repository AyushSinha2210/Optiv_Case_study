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
