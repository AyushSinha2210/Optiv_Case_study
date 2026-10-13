"""Member 3 redaction, verification, and release-gate API."""

from .service import redact_and_validate as service_redact_and_validate
from .redactor import (
    RedactionError,
    Redactor,
    apply_redactions,
    redact_text,
    validate_spans,
    redact_and_validate,
)
from .schemas import RedactionFinding, RedactionResult

__all__ = [
    "RedactionFinding",
    "RedactionResult",
    "redact_and_validate",
    "service_redact_and_validate",
    "Redactor",
    "apply_redactions",
    "redact_text",
    "validate_spans",
    "RedactionError",
]
