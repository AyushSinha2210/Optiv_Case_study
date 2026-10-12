"""Redaction, Verification & Release Gate Module.

Produces Contract C RedactionResult from Contract A ExtractedDocument and Contract B DetectionResult.
"""

from .redactor import redact_and_validate, Redactor

__all__ = ["redact_and_validate", "Redactor"]
