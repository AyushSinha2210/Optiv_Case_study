"""Redaction, Verification & Release Gate Module (Member 3: Yash Jhinkwan).

Produces Contract C RedactionResult from Contract B DetectionResult.
"""

from .redactor import (
    RedactionApplication,
    RedactionError,
    Redactor,
    ValidatedSpan,
    apply_redactions,
    redact_text,
    redact_and_validate,
)
from .schemas import RedactionFinding, RedactionResult
from .service import redact_and_validate as service_redact_and_validate

__all__ = [
    "RedactionFinding",
    "RedactionResult",
    "redact_and_validate",
    "service_redact_and_validate",
    "Redactor",
    "redact_text",
    "apply_redactions",
    "RedactionError",
    "ValidatedSpan",
    "RedactionApplication",
]
