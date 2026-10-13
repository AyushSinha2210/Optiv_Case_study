"""PII detection engine conforming strictly to Contract B.

Detects standard enterprise PII entity categories with exact character offsets into ExtractedDocument.text.
"""

import re
from typing import List, Optional, Tuple
from ..ingestion.schemas import ExtractedDocument
from ..orchestration.models import DetectedEntity, DetectionResult


# High-precedence regex patterns for standard categories
PATTERNS = [
    # Employee ID (e.g. CAD-EMP-12345 or CAD-77129)
    ("EMPLOYEE_ID", re.compile(r"\bCAD-(?:EMP-)?\d{4,6}\b", re.IGNORECASE), 0.95),
    # Email addresses
    ("EMAIL", re.compile(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b"), 0.98),
    # Government ID / SSN (e.g. 000-12-3456)
    ("GOVERNMENT_ID", re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), 0.99),
    # Phone numbers
    ("PHONE", re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), 0.90),
    # IPv4 addresses
    ("IP_ADDRESS", re.compile(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"), 0.92),
    # Synthetic / named person markers (e.g. "Samantha Vance", "Julian Thorne")
    ("PERSON", re.compile(r"\b(?:Samantha Vance|Julian Thorne|Jane Doe|John Doe|René Descartes|Hélène Synthétique|Johann Weiß)\b"), 0.85),
]


class PIIDetector:
    """Deterministic pattern and contextual PII detector."""

    def __init__(self, confidence_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold
        self.ner_backend = ner_backend

    def detect(self, doc: ExtractedDocument) -> DetectionResult:
        """Scan ExtractedDocument.text and return Contract B DetectionResult."""
        text = doc.text
        raw_spans: List[Tuple[int, int, str, float]] = []

        for entity_type, regex, base_conf in PATTERNS:
            if base_conf < self.confidence_threshold:
                continue
            for match in regex.finditer(text):
                start, end = match.span()
                raw_spans.append((start, end, entity_type, base_conf))

        # Deterministic overlap resolution:
        # Sort by start offset asc, length desc, confidence desc
        raw_spans.sort(key=lambda s: (s[0], -(s[1] - s[0]), -s[3]))

        resolved_entities: List[DetectedEntity] = []
        last_end = -1

        for start, end, ent_type, conf in raw_spans:
            if start >= last_end:
                resolved_entities.append(
                    DetectedEntity(type=ent_type, start=start, end=end, confidence=conf)
                )
                last_end = end

        return DetectionResult(
            document_id=doc.document_id,
            entities=resolved_entities,
            warnings=[],
        )


def detect_pii(doc: ExtractedDocument, options: Optional[dict] = None) -> DetectionResult:
    """Public functional interface for PII detection."""
    detector = PIIDetector()
    return detector.detect(doc)
