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
    """Return a fast, high-precision contextual person name detector supporting all casings and Indian/international names."""
    import re
    from .pattern_detector import _is_valid_person_name, _COMMON_FIRST_NAMES, _COMMON_LAST_NAMES

    patterns = (
        re.compile(r"(?i)\bprepared[ \t]+by[ \t]+([a-zA-Z'.-]+(?:[ \t]+[a-zA-Z'.-]+){1,3})\b"),
        re.compile(r"(?i)\bescalate[ \t]+to[ \t]+([a-zA-Z'.-]+(?:[ \t]+[a-zA-Z'.-]+){1,3})\b"),
        re.compile(r"(?i)\bcustomer[ \t]+([a-zA-Z'.-]+(?:[ \t]+[a-zA-Z'.-]+){1,3})\b"),
        re.compile(r"(?i)\bissued[ \t]+to[ \t]+([a-zA-Z'.-]+(?:[ \t]+[a-zA-Z'.-]+){1,3})\b"),
        re.compile(r"(?i)\bcontact[ \t]+([a-zA-Z'.-]+(?:[ \t]+[a-zA-Z'.-]+){1,3})[ \t]+(?:at|on|via)\b"),
        re.compile(r"(?i)\b([a-zA-Z'.-]+(?:[ \t]+[a-zA-Z'.-]+){1,3})[ \t]+\((?:CAD-)?EMP-\d+\)"),
        re.compile(r"(?i)\breviewed[ \t]+by[ \t]+([a-zA-Z'.-]+(?:[ \t]+[a-zA-Z'.-]+){1,3})\b"),
        re.compile(r"(?i)\bsubmitted[ \t]+by[ \t]+([a-zA-Z'.-]+(?:[ \t]+[a-zA-Z'.-]+){1,3})\b"),
        re.compile(r"(?i)\bassigned[ \t]+to[ \t]+([a-zA-Z'.-]+(?:[ \t]+[a-zA-Z'.-]+){1,3})\b"),
        re.compile(r"(?i)\breported[ \t]+by[ \t]+([a-zA-Z'.-]+(?:[ \t]+[a-zA-Z'.-]+){1,3})\b"),
    )

    list_header_pat = re.compile(
        r"(?i)\b(?:team[ \t]*members?|members?|attendees?|participants?|contributors?|authors?|"
        r"reviewers?|engineers?|developers?|candidates?|names?|contacts?)"
        r"[ \t]*[:#-]\s*([^\r\n.]+)"
    )
    coord_pat = re.compile(
        r"\b([a-zA-Z'.-]+(?:[ \t]+[a-zA-Z'.-]+){1,2})"
        r"\s+(?:and|&|with|or)\s+"
        r"([a-zA-Z'.-]+(?:[ \t]+[a-zA-Z'.-]+){1,2})\b"
    )

    gazetteer_pat = re.compile(r"\b([a-zA-Z]{2,20})[ \t]+([a-zA-Z]{2,20})\b")

    def backend(segment: str) -> list[tuple[str, int, int, float]]:
        results: list[tuple[str, int, int, float]] = []
        covered_ranges: list[tuple[int, int]] = []

        for pat in patterns:
            for m in pat.finditer(segment):
                name_val = m.group(1).strip()
                words = name_val.split()
                cand_name = None
                for l in range(min(len(words), 3), 1, -1):
                    sub = " ".join(words[:l])
                    if _is_valid_person_name(sub, allow_lowercase=True):
                        cand_name = sub
                        break
                if cand_name:
                    v_idx = name_val.find(cand_name)
                    start = m.start(1) + (v_idx if v_idx >= 0 else 0)
                    end = start + len(cand_name)
                    if not any(max(start, cs) < min(end, ce) for cs, ce in covered_ranges):
                        results.append(("PERSON", start, end, 0.88))
                        covered_ranges.append((start, end))

        # Multi-name lists & team headers
        for lm in list_header_pat.finditer(segment):
            raw_list = lm.group(1)
            list_offset = lm.start(1)
            delims = re.compile(r"\s*(?:,\s*(?:and|&|or)?\s*|\s+(?:and|&|or)\s+)\s*")
            curr_pos = 0
            for part in delims.split(raw_list):
                part_clean = part.strip(" ,;:\t")
                if not part_clean:
                    continue
                p_idx = raw_list.find(part_clean, curr_pos)
                if p_idx >= 0:
                    curr_pos = p_idx + len(part_clean)
                    if _is_valid_person_name(part_clean, allow_lowercase=True):
                        start = list_offset + p_idx
                        end = start + len(part_clean)
                        if not any(max(start, cs) < min(end, ce) for cs, ce in covered_ranges):
                            results.append(("PERSON", start, end, 0.90))
                            covered_ranges.append((start, end))

        # Coordinated name pairs in running text
        for cm in coord_pat.finditer(segment):
            raw_n1 = cm.group(1).strip()
            raw_n2 = cm.group(2).strip()
            words1 = raw_n1.split()
            words2 = raw_n2.split()
            c1 = None
            for l in range(min(len(words1), 3), 1, -1):
                sub = " ".join(words1[:l])
                if _is_valid_person_name(sub, allow_lowercase=True):
                    c1 = sub
                    break
            c2 = None
            for l in range(min(len(words2), 3), 1, -1):
                sub = " ".join(words2[:l])
                if _is_valid_person_name(sub, allow_lowercase=True):
                    c2 = sub
                    break
            if c1 and c2:
                idx1 = raw_n1.find(c1)
                s1 = cm.start(1) + (idx1 if idx1 >= 0 else 0)
                e1 = s1 + len(c1)
                if not any(max(s1, cs) < min(e1, ce) for cs, ce in covered_ranges):
                    results.append(("PERSON", s1, e1, 0.89))
                    covered_ranges.append((s1, e1))
                idx2 = raw_n2.find(c2)
                s2 = cm.start(2) + (idx2 if idx2 >= 0 else 0)
                e2 = s2 + len(c2)
                if not any(max(s2, cs) < min(e2, ce) for cs, ce in covered_ranges):
                    results.append(("PERSON", s2, e2, 0.89))
                    covered_ranges.append((s2, e2))

        # Gazetteer matching for known names across any casing
        for gm in gazetteer_pat.finditer(segment):
            f_val = gm.group(1).upper()
            l_val = gm.group(2).upper()
            if f_val in _COMMON_FIRST_NAMES and (l_val in _COMMON_LAST_NAMES or len(l_val) >= 3):
                cand = gm.group(0).strip()
                if _is_valid_person_name(cand, allow_lowercase=True):
                    start = gm.start()
                    end = gm.end()
                    if not any(max(start, cs) < min(end, ce) for cs, ce in covered_ranges):
                        results.append(("PERSON", start, end, 0.86))
                        covered_ranges.append((start, end))

        return results


    return backend


def get_default_ner_backend() -> Optional[NerBackend]:
    """Return an ensemble NER backend combining spaCy (if available) with high-precision contextual NER."""
    spacy_backend = load_spacy_backend()
    contextual_backend = load_contextual_ner_backend()

    if spacy_backend is None:
        return contextual_backend

    def ensemble_backend(segment: str) -> list[tuple[str, int, int, float]]:
        merged: list[tuple[str, int, int, float]] = []
        covered_ranges: list[tuple[int, int]] = []

        # 1. High-precision contextual & gazetteer detections take precedence
        for label, start, end, score in contextual_backend(segment):
            merged.append((label, start, end, score))
            covered_ranges.append((start, end))

        # 2. Add non-overlapping spaCy predictions
        for label, start, end, score in spacy_backend(segment):
            if label in NER_LABEL_MAP:
                if not any(max(start, cs) < min(end, ce) for cs, ce in covered_ranges):
                    merged.append((label, start, end, score))
                    covered_ranges.append((start, end))

        return merged

    return ensemble_backend



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
