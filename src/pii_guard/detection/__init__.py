"""PII Detection & Classification Module.

Produces Contract B DetectionResult from Contract A ExtractedDocument.
"""

from .detector import detect_pii, PIIDetector

__all__ = ["detect_pii", "PIIDetector"]
