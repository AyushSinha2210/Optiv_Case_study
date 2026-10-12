"""Unit tests for the ingestion command-line interface (CLI)."""

import sys
import json
import subprocess
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "ingestion"


def test_cli_human_readable_output():
    """Verify standard CLI invocation outputs formatted document summary."""
    cmd = [
        sys.executable,
        "-m",
        "src.pii_guard.ingestion",
        str(FIXTURES_DIR / "sample.docx"),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    out = res.stdout
    assert "Document ID:" in out
    assert "Source Type:        docx" in out
    assert "Status:             success" in out
    assert "Pages / Slides:     1" in out


def test_cli_json_output():
    """Verify CLI with --json outputs valid JSON matching ExtractedDocument contract."""
    cmd = [
        sys.executable,
        "-m",
        "src.pii_guard.ingestion",
        str(FIXTURES_DIR / "sample.docx"),
        "--json",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(res.stdout)
    assert "document_id" in data
    assert data["source_type"] == "docx"
    assert data["extraction_status"] == "success"
    assert isinstance(data["pages"], list)
    assert len(data["pages"]) == 1
    assert "REDACTED_FOR_DISPLAY" in data["text"]


def test_cli_show_text_flag():
    """Verify CLI with --show-text outputs the exact extracted text."""
    cmd = [
        sys.executable,
        "-m",
        "src.pii_guard.ingestion",
        str(FIXTURES_DIR / "sample.docx"),
        "--show-text",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert "--- Extracted Text ---" in res.stdout
    assert "Third-Party Data Handling Policy" in res.stdout
