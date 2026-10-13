"""Redaction, Verification & Release Gate Module (Member 3: Yash Jhinkwan).

Public API:
    redact_and_validate -> unified redaction, verification, and fail-closed release gate
    Redactor -> OOP redaction and verification runner
    redact_text -> functional single-string redaction helper
    apply_redactions -> right-to-left masking application
    validate_spans -> span offset boundary and overlap checks
    RedactionResult -> Contract C model
    RedactionFinding -> sanitized finding detail
    RedactionError -> validation and masking exception
"""

from .redactor import (
    RedactionApplication,
    RedactionError,
    Redactor,
    ValidatedSpan,
    apply_redactions,
    redact_text,
    validate_spans,
)
from .schemas import RedactionFinding, RedactionResult
from .service import redact_and_validate

__all__ = [
    "RedactionFinding",
    "RedactionResult",
    "redact_and_validate",
    "Redactor",
    "redact_text",
    "apply_redactions",
    "validate_spans",
    "RedactionError",
    "ValidatedSpan",
    "RedactionApplication",
]
