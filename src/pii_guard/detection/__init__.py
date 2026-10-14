"""PII detection and classification (Member 2: Avishi Sharma).

Produces Contract B DetectionResult from Contract A ExtractedDocument.

Public API:
    detect_pii(document, ner_backend=None) -> DetectionResult
    load_spacy_backend() -> optional NER backend for PERSON entities
    PIIDetector -> deterministic pattern and contextual PII detector wrapper
"""

from .detector import PIIDetector, detect_pii
from .ner_detector import get_default_ner_backend, load_contextual_ner_backend, load_spacy_backend
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
    "load_contextual_ner_backend",
    "get_default_ner_backend",
    "DetectedEntity",
    "DetectionResult",
    "DetectionWarning",
    "DetectionInputError",
    "PII_TYPES",
]

