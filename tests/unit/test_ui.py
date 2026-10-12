"""Unit tests for Streamlit application validation logic and startup."""

import pytest
from unittest.mock import MagicMock
from app import validate_uploaded_file, MAX_FILE_SIZE_BYTES


def test_validate_uploaded_file_valid_txt():
    """Valid text document passes upload validation."""
    mock_file = MagicMock()
    mock_file.name = "annual_audit.txt"
    mock_file.size = 1024

    is_valid, err = validate_uploaded_file(mock_file)
    assert is_valid is True
    assert err is None


def test_validate_uploaded_file_valid_docx():
    """Valid DOCX document passes upload validation."""
    mock_file = MagicMock()
    mock_file.name = "report.docx"
    mock_file.size = 50000

    is_valid, err = validate_uploaded_file(mock_file)
    assert is_valid is True
    assert err is None


def test_validate_uploaded_file_unsupported_extension():
    """Unsupported executable or script extension is rejected."""
    mock_file = MagicMock()
    mock_file.name = "malware.exe"
    mock_file.size = 2048

    is_valid, err = validate_uploaded_file(mock_file)
    assert is_valid is False
    assert "Unsupported file extension" in err


def test_validate_uploaded_file_oversized():
    """File exceeding MAX_FILE_SIZE_BYTES is rejected."""
    mock_file = MagicMock()
    mock_file.name = "giant.pdf"
    mock_file.size = MAX_FILE_SIZE_BYTES + 1024

    is_valid, err = validate_uploaded_file(mock_file)
    assert is_valid is False
    assert "exceeds maximum allowed size" in err


def test_validate_uploaded_file_empty():
    """0-byte file is rejected."""
    mock_file = MagicMock()
    mock_file.name = "zero.pdf"
    mock_file.size = 0

    is_valid, err = validate_uploaded_file(mock_file)
    assert is_valid is False
    assert "0 bytes" in err


def test_app_imports_cleanly():
    """Verifies app.py module syntax and top-level dependencies load without error."""
    import app
    assert hasattr(app, "main")
    assert hasattr(app, "validate_uploaded_file")
