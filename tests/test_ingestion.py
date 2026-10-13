"""Comprehensive test suite for the Ingestion, OCR, and Quality module."""

import logging
from pathlib import Path
import pytest

from src.pii_guard.ingestion import extract_document, IngestionConfig
from src.pii_guard.ingestion.normalize import normalize_text
from src.pii_guard.ingestion.quality import calculate_quality_metrics, GroundTruthStructure

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "ingestion"


@pytest.fixture(scope="session", autouse=True)
def ensure_fixtures_exist():
    """Ensure all synthetic test fixtures are generated prior to running tests."""
    from tests.fixtures.ingestion.make_fixtures import generate_all_fixtures
    if not (FIXTURES_DIR / "clean_text.pdf").exists():
        generate_all_fixtures()


# ---------------------------------------------------------------------------
# 1. Supported Formats & Extraction Status Tests
# ---------------------------------------------------------------------------

def test_extract_clean_text_pdf():
    """Verify digital text PDF extraction."""
    doc = extract_document(str(FIXTURES_DIR / "clean_text.pdf"))
    assert doc.extraction_status == "success"
    assert doc.source_type == "pdf"
    assert len(doc.pages) == 2
    assert "Cadence Financial Group" in doc.text
    assert "Executive Summary" in doc.text
    assert "Compliance Sign-off" in doc.text


def test_extract_scanned_pdf():
    """Verify image-only scanned PDF uses OCR and returns valid text."""
    doc = extract_document(str(FIXTURES_DIR / "scanned_page.pdf"))
    assert doc.extraction_status in ("success", "partial")
    assert doc.source_type in ("scanned_pdf", "pdf")
    assert len(doc.pages) == 1
    assert doc.pages[0].method in ("ocr", "mixed")
    assert "Account Authorization" in doc.text or "Julian Thorne" in doc.text or "CAD-77129" in doc.text


def test_extract_rotated_scanned_pdf():
    """Verify rotated scanned PDF is handled gracefully with OSD rotation."""
    doc = extract_document(str(FIXTURES_DIR / "rotated_scanned.pdf"))
    assert doc.extraction_status in ("success", "partial")
    assert len(doc.pages) == 1


def test_extract_mixed_pdf():
    """Verify mixed digital and scanned PDF handles both methods across pages."""
    doc = extract_document(str(FIXTURES_DIR / "mixed.pdf"))
    assert doc.extraction_status in ("success", "partial")
    assert len(doc.pages) == 2
    assert doc.pages[0].method == "native"
    assert doc.pages[1].method in ("ocr", "mixed")


def test_extract_sample_docx():
    """Verify Word document paragraphs and tables in sequential document order."""
    doc = extract_document(str(FIXTURES_DIR / "sample.docx"))
    assert doc.extraction_status == "success"
    assert doc.source_type == "docx"
    assert len(doc.pages) == 1
    assert "Cadence Internal Controls" in doc.text  # Header
    assert "Third-Party Data Handling Policy" in doc.text
    assert "Cloud Storage | High | KMS Encryption" in doc.text  # Table
    assert "Page 1 | Confidential" in doc.text  # Footer


def test_extract_sample_pptx():
    """Verify presentation extraction with slide titles, tables, and speaker notes."""
    doc = extract_document(str(FIXTURES_DIR / "sample.pptx"))
    assert doc.extraction_status == "success"
    assert doc.source_type == "pptx"
    assert len(doc.pages) == 2
    assert doc.pages[0].label == "slide"
    assert "Cadence Financial Group TPRM Briefing" in doc.text
    assert "Vendor Risk Distribution" in doc.text
    assert "Apex Systems | Audited" in doc.text
    assert "--- Speaker Notes ---" in doc.text


def test_extract_utf8_and_latin1_txt():
    """Verify plain text extraction with encoding detection."""
    doc_utf8 = extract_document(str(FIXTURES_DIR / "utf8.txt"))
    assert doc_utf8.extraction_status == "success"
    assert "René Descartes" in doc_utf8.text

    doc_latin1 = extract_document(str(FIXTURES_DIR / "latin1.txt"))
    assert doc_latin1.extraction_status == "success"
    assert "Zürich" in doc_latin1.text or "Zurich" in doc_latin1.text


# ---------------------------------------------------------------------------
# 2. Security, Malformed Artifacts & Fail-Closed Tests
# ---------------------------------------------------------------------------

def test_fail_closed_empty_file():
    """Zero-byte files must immediately fail without crashing."""
    doc = extract_document(str(FIXTURES_DIR / "empty.txt"))
    assert doc.extraction_status == "failed"
    assert any(w.code == "ERR_EMPTY_FILE" for w in doc.warnings)
    assert doc.text == ""


def test_fail_closed_corrupt_file():
    """Corrupted files must return status='failed' and structured error codes."""
    doc = extract_document(str(FIXTURES_DIR / "corrupt.pdf"))
    assert doc.extraction_status == "failed"
    assert any("CORRUPT" in w.code for w in doc.warnings)


def test_fail_closed_renamed_executable():
    """Executable binary renamed to .pdf must be rejected via magic bytes."""
    doc = extract_document(str(FIXTURES_DIR / "renamed_exe.pdf"))
    assert doc.extraction_status == "failed"
    assert any("EXECUTABLE" in w.code or "SIGNATURE" in w.code for w in doc.warnings)


def test_fail_closed_encrypted_pdf():
    """Password-protected PDFs must fail with an encryption warning code."""
    doc = extract_document(str(FIXTURES_DIR / "encrypted.pdf"))
    assert doc.extraction_status == "failed"
    assert any("PASSWORD" in w.code or "ENCRYPTED" in w.code for w in doc.warnings)


def test_fail_closed_zip_bomb_docx():
    """Zip bomb artifacts must be intercepted by uncompressed ratio guard."""
    cfg = IngestionConfig(zip_bomb_max_ratio=50.0)
    doc = extract_document(str(FIXTURES_DIR / "zip_bomb.docx"), config=cfg)
    assert doc.extraction_status == "failed"
    assert any("ZIP_BOMB" in w.code for w in doc.warnings)


def test_fail_closed_oversized_file(tmp_path):
    """Files exceeding size limit must fail closed."""
    oversized = tmp_path / "huge.txt"
    oversized.write_text("A" * 1024)
    cfg = IngestionConfig(max_file_size_bytes=500)
    doc = extract_document(str(oversized), config=cfg)
    assert doc.extraction_status == "failed"
    assert any(w.code == "ERR_FILE_OVERSIZED" for w in doc.warnings)


def test_fail_closed_nonexistent_file():
    """Nonexistent paths must return failed status without throwing exceptions."""
    doc = extract_document("nonexistent_path_to_file.pdf")
    assert doc.extraction_status == "failed"
    assert any(w.code == "ERR_FILE_NOT_FOUND" for w in doc.warnings)


def test_fail_closed_none_or_invalid_path():
    """None and invalid path types must return failed status without throwing exceptions."""
    doc = extract_document(None)
    assert doc.extraction_status == "failed"
    assert any(w.code == "ERR_INVALID_FILE_PATH" for w in doc.warnings)


# ---------------------------------------------------------------------------
# 3. Text Rules, Normalization & Offset Integrity
# ---------------------------------------------------------------------------

def test_normalization_idempotence():
    """Normalizing text twice must return identical output."""
    raw = "  Hello World\r\n\r\nLine 2 with trailing spaces   \n\x00Null\x07"
    norm1 = normalize_text(raw)
    norm2 = normalize_text(norm1)
    assert norm1 == norm2
    assert "\x00" not in norm1
    assert "\r" not in norm1


def test_page_offset_integrity():
    """Verify pages[i].start and pages[i].end slice into text with 100% precision."""
    doc = extract_document(str(FIXTURES_DIR / "clean_text.pdf"))
    assert doc.extraction_status == "success"
    assert len(doc.pages) == 2

    p0 = doc.pages[0]
    p1 = doc.pages[1]

    # Verify slices
    page0_text = doc.text[p0.start : p0.end]
    page1_text = doc.text[p1.start : p1.end]

    assert "Cadence Financial Group" in page0_text
    assert "Compliance Sign-off" in page1_text
    assert len(page0_text) == p0.char_count
    assert len(page1_text) == p1.char_count

    # Verify separator
    assert doc.text[p0.end : p1.start] == "\f"


def test_extraction_determinism():
    """Running extraction twice on the same file produces identical output."""
    doc1 = extract_document(str(FIXTURES_DIR / "sample.docx"))
    doc2 = extract_document(str(FIXTURES_DIR / "sample.docx"))
    assert doc1.text == doc2.text
    assert len(doc1.pages) == len(doc2.pages)
    assert doc1.pages[0].start == doc2.pages[0].start
    assert doc1.pages[0].end == doc2.pages[0].end


# ---------------------------------------------------------------------------
# 4. Privacy & Telemetry Guard
# ---------------------------------------------------------------------------

def test_no_document_text_in_logs_or_warnings(caplog):
    """Ensure no extracted text or synthetic PII leaks into logs or warning messages."""
    with caplog.at_level(logging.DEBUG):
        doc = extract_document(str(FIXTURES_DIR / "clean_text.pdf"))

    # Verify warnings contain no document text
    for w in doc.warnings:
        assert "Cadence" not in w.message
        assert "Samantha Vance" not in w.message

    # Verify logs contain no document text
    log_text = caplog.text
    assert "svance@cadencefg.com" not in log_text
    assert "Samantha Vance" not in log_text


# ---------------------------------------------------------------------------
# 5. Extraction Quality & Structure Retention Score (>= 80% Requirement)
# ---------------------------------------------------------------------------

def test_quality_metrics_structure_score_above_80():
    """Verify that extraction achieves >= 80% structure retention on synthetic fixtures."""
    doc = extract_document(str(FIXTURES_DIR / "sample.docx"))

    ground_truth = GroundTruthStructure(
        expected_text="Cadence Internal Controls Policy Document Third-Party Data Handling Policy",
        expected_pages=1,
        headings=["Third-Party Data Handling Policy"],
        paragraphs=[
            "Employees are strictly forbidden from sharing customer PII with unverified vendors.",
            "Exceptions must be approved by the Chief Information Security Officer.",
        ],
        table_rows=[
            "Cloud Storage | High | KMS Encryption",
            "Email Relay | Medium | TLS 1.3",
        ],
        reading_order_anchors=[
            "Third-Party Data Handling Policy",
            "Cloud Storage",
            "Exceptions must be approved",
        ],
    )

    metrics = calculate_quality_metrics(doc, ground_truth)
    assert metrics.structure_score >= 80.0, f"Structure score {metrics.structure_score}% < 80.0%"
    assert metrics.passes_threshold(80.0)
    assert metrics.completeness >= 80.0
