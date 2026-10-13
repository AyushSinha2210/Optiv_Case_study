<<<<<<< HEAD
"""Member 3 redaction, verification, and release-gate API."""
=======
"""Redaction, Verification & Release Gate Module (Member 3: Yash Jhinkwan).
>>>>>>> origin/feature/member5-integration

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

<<<<<<< HEAD
=======
from .redactor import RedactionApplication, RedactionError, Redactor, ValidatedSpan, apply_redactions, redact_text
from .schemas import RedactionFinding, RedactionResult
from .service import redact_and_validate

>>>>>>> origin/feature/member5-integration
__all__ = [
    "RedactionFinding",
    "RedactionResult",
    "redact_and_validate",
<<<<<<< HEAD
    "service_redact_and_validate",
    "Redactor",
    "apply_redactions",
    "redact_text",
    "validate_spans",
    "RedactionError",
=======
    "Redactor",
    "redact_text",
    "apply_redactions",
    "RedactionError",
    "ValidatedSpan",
    "RedactionApplication",
>>>>>>> origin/feature/member5-integration
]
