"""Structured error hierarchy and sanitized exception handling.

PRIVACY MANDATE:
Exceptions raised or caught in the orchestration layer must NEVER expose:
- Raw document text or snippets
- Detected personal identifiers (names, emails, phones, SSNs, account numbers)
- Internal filesystem paths or directory hierarchies
- Secrets, tokens, or credentials
- Raw Python stack traces in user-facing messages
"""

import re
from typing import Optional


def sanitize_error_message(message: str) -> str:
    """Scrub absolute filesystem paths, tokens, and suspicious PII from error strings."""
    if not message:
        return "An internal error occurred"

    sanitized = str(message)

    # 1. Strip Windows paths (e.g. C:\Users\... or D:\Dev_Projects\...)
    sanitized = re.sub(r"[a-zA-Z]:\\[^\s\<\>\"\'\:]+", "[REDACTED_PATH]", sanitized)
    # Strip POSIX paths (e.g. /home/... or /usr/...)
    sanitized = re.sub(r"/(?:[a-zA-Z0-9_\-\.]+/)+[a-zA-Z0-9_\-\.]*", "[REDACTED_PATH]", sanitized)

    # 2. Strip obvious email addresses
    sanitized = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[REDACTED_EMAIL]", sanitized)

    # 3. Strip phone numbers (standard US/international formats)
    sanitized = re.sub(r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b", "[REDACTED_PHONE]", sanitized)

    # 4. Strip SSN-like or Tax ID patterns (xxx-xx-xxxx)
    sanitized = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[REDACTED_GOV_ID]", sanitized)

    # 5. Collapse excessive whitespace
    sanitized = " ".join(sanitized.split())

    return sanitized


class PipelineError(Exception):
    """Base exception for all pipeline errors with safe error codes."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_PIPELINE_ERROR",
        safe_message: Optional[str] = None,
    ):
        self.error_code = error_code
        self.safe_message = sanitize_error_message(safe_message or message)
        super().__init__(self.safe_message)


class ValidationError(PipelineError):
    """Input validation failure (e.g., malformed file or zero bytes)."""

    def __init__(self, message: str, error_code: str = "ERR_VALIDATION_FAILED", safe_message: Optional[str] = None):
        super().__init__(message, error_code=error_code, safe_message=safe_message)


class UnsupportedFileTypeError(ValidationError):
    """File extension or magic byte signature is not supported."""

    def __init__(self, message: str = "File format is not supported", error_code: str = "ERR_UNSUPPORTED_FORMAT"):
        super().__init__(message, error_code=error_code)


class FileTooLargeError(ValidationError):
    """Uploaded file exceeds configured maximum size limit."""

    def __init__(self, message: str = "File exceeds maximum permitted size", error_code: str = "ERR_FILE_OVERSIZED"):
        super().__init__(message, error_code=error_code)


class DocumentReadError(PipelineError):
    """File could not be read or opened."""

    def __init__(self, message: str = "Document could not be read", error_code: str = "ERR_READ_FAILED"):
        super().__init__(message, error_code=error_code)


class ExtractionError(PipelineError):
    """Extraction stage failure."""

    def __init__(self, message: str = "Document extraction failed", error_code: str = "ERR_EXTRACTION_FAILED"):
        super().__init__(message, error_code=error_code)


class DetectionError(PipelineError):
    """Detection stage failure."""

    def __init__(self, message: str = "PII detection failed", error_code: str = "ERR_DETECTION_FAILED"):
        super().__init__(message, error_code=error_code)


class RedactionError(PipelineError):
    """Redaction stage failure."""

    def __init__(self, message: str = "Document redaction failed", error_code: str = "ERR_REDACTION_FAILED"):
        super().__init__(message, error_code=error_code)


class VerificationError(PipelineError):
    """Verification stage failure or post-redaction leakage detection."""

    def __init__(self, message: str = "Verification failed", error_code: str = "ERR_VERIFICATION_FAILED"):
        super().__init__(message, error_code=error_code)


class ReleaseGateBlockedError(PipelineError):
    """Document release is forbidden by policy."""

    def __init__(self, message: str = "Document release blocked by verification gate", error_code: str = "WARN_RELEASE_BLOCKED"):
        super().__init__(message, error_code=error_code)


class ArtifactAccessError(PipelineError):
    """Unauthorized or invalid attempt to access a protected artifact."""

    def __init__(self, message: str = "Artifact access denied or unavailable", error_code: str = "ERR_ARTIFACT_ACCESS_DENIED"):
        super().__init__(message, error_code=error_code)


class InternalProcessingError(PipelineError):
    """Unhandled internal pipeline exception."""

    def __init__(self, message: str = "An unexpected processing error occurred", error_code: str = "ERR_INTERNAL_ERROR"):
        super().__init__(message, error_code=error_code)


class InvalidStateTransitionError(PipelineError):
    """Attempted illegal state machine transition."""

    def __init__(self, message: str = "Illegal pipeline state transition", error_code: str = "ERR_INVALID_TRANSITION"):
        super().__init__(message, error_code=error_code)
