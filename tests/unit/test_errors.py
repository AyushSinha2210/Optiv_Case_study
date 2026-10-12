"""Unit tests for pipeline error classes and message sanitization."""

import pytest
from src.pii_guard.orchestration.errors import (
    PipelineError,
    ValidationError,
    UnsupportedFileTypeError,
    FileTooLargeError,
    DocumentReadError,
    ExtractionError,
    DetectionError,
    RedactionError,
    VerificationError,
    ReleaseGateBlockedError,
    ArtifactAccessError,
    InternalProcessingError,
    InvalidStateTransitionError,
    sanitize_error_message,
)


def test_sanitize_error_message_strips_windows_paths():
    """Windows filesystem paths must be replaced with [REDACTED_PATH]."""
    raw = "Failed to load document at C:\\Users\\Administrator\\SecretDocs\\customer_list.pdf"
    clean = sanitize_error_message(raw)
    assert "C:\\Users" not in clean
    assert "customer_list.pdf" not in clean
    assert "[REDACTED_PATH]" in clean


def test_sanitize_error_message_strips_unix_paths():
    """UNIX paths must be replaced with [REDACTED_PATH]."""
    raw = "Corrupt buffer in /var/data/confidential/passwords.txt"
    clean = sanitize_error_message(raw)
    assert "/var/data" not in clean
    assert "[REDACTED_PATH]" in clean


def test_sanitize_error_message_strips_emails():
    """Emails embedded in exception strings must be redacted."""
    raw = "Failed processing record for john.doe@enterprise.com with internal error"
    clean = sanitize_error_message(raw)
    assert "john.doe@enterprise.com" not in clean
    assert "[REDACTED_EMAIL]" in clean


def test_sanitize_error_message_strips_phones_and_ssns():
    """Phone numbers and SSN patterns must be redacted."""
    raw = "Customer phone 415-555-0199 and SSN 123-45-6789 encountered"
    clean = sanitize_error_message(raw)
    assert "415-555-0199" not in clean
    assert "123-45-6789" not in clean
    assert "[REDACTED_PHONE]" in clean
    assert "[REDACTED_GOV_ID]" in clean


def test_error_hierarchy_inheritance():
    """All custom error classes must inherit from PipelineError."""
    assert issubclass(ValidationError, PipelineError)
    assert issubclass(UnsupportedFileTypeError, ValidationError)
    assert issubclass(FileTooLargeError, ValidationError)
    assert issubclass(DocumentReadError, PipelineError)
    assert issubclass(ExtractionError, PipelineError)
    assert issubclass(DetectionError, PipelineError)
    assert issubclass(RedactionError, PipelineError)
    assert issubclass(VerificationError, PipelineError)
    assert issubclass(ReleaseGateBlockedError, PipelineError)
    assert issubclass(ArtifactAccessError, PipelineError)
    assert issubclass(InternalProcessingError, PipelineError)
    assert issubclass(InvalidStateTransitionError, PipelineError)


def test_error_instantiation_sanitizes_message():
    """Instantiating an error automatically sanitizes its public message."""
    err = ExtractionError("Crash while processing D:\\Sensitive\\Records\\file.pdf for test@acme.com")
    assert "D:\\Sensitive" not in str(err)
    assert "test@acme.com" not in str(err)
    assert err.error_code == "ERR_EXTRACTION_FAILED"
