"""PII detection and classification (Member 2: Avishi Sharma).

Public API:
    detect_pii(document, ner_backend=None) -> DetectionResult
    load_spacy_backend() -> optional NER backend for PERSON entities
"""

from .detector import detect_pii, PIIDetector
from .ner_detector import load_spacy_backend
from .schemas import (
    PII_TYPES,
    DetectedEntity,
    DetectionInputError,
    DetectionResult,
    DetectionWarning,
)

__all__ = [
    "detect_pii",
    "PIIDetector",
    "load_spacy_backend",
    "DetectedEntity",
    "DetectionResult",
    "DetectionWarning",
    "DetectionInputError",
    "PII_TYPES",
]
