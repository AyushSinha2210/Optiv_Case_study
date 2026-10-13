"""Comprehensive test suite for parsing and end-to-end processing of all document formats.

Validates ingestion, extraction, offsets, PII detection, redaction, verification,
and fail-closed security invariants across:
- PowerPoint presentations (.pptx) with slides, tables, and notes
- Multi-page digital and scanned PDF documents (.pdf)
- Structured Word documents (.docx) with tables and headers
- Plain text (.txt) in UTF-8, UTF-8 BOM, UTF-16 LE, and international Unicode
- Security boundary files (corrupted headers, renamed executables, zero bytes)
"""

import shutil
from pathlib import Path
import pytest

TESSERACT_AVAILABLE = shutil.which("tesseract") is not None

from src.pii_guard.ingestion import extract_document, IngestionConfig
from src.pii_guard.ingestion.validator import validate_file
from src.pii_guard.orchestration.pipeline import process_document
from src.pii_guard.orchestration.state import PipelineStage
from src.pii_guard.reporting.audit import AuditTrail
from src.pii_guard.orchestration.artifacts import ArtifactManager

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "demo_samples" / "fixtures"


@pytest.fixture(scope="session", autouse=True)
def ensure_demo_fixtures_exist():
    """Ensure all synthetic demonstration fixtures are generated prior to running tests."""
    from demo_tools.generate_synthetic_samples import SyntheticSampleGenerator
    if not (FIXTURES_DIR / "11_quarterly_briefing.pptx").exists():
        SyntheticSampleGenerator(seed=42).generate_all()


# ---------------------------------------------------------------------------
# 1. PowerPoint (.pptx) Parsing Tests
# ---------------------------------------------------------------------------

def test_parse_quarterly_briefing_pptx():
    """Verify PPTX extraction preserves slide hierarchy, tables, and notes."""
    path = FIXTURES_DIR / "11_quarterly_briefing.pptx"
    assert path.exists(), f"Missing fixture: {path}"

    doc = extract_document(str(path))
    assert doc.extraction_status == "success"
    assert doc.source_type == "pptx"
    assert len(doc.pages) == 3

    # Check slide 1 title and metadata
    assert "Cadence Financial Group - Quarterly Client Briefing" in doc.text
    assert doc.pages[0].label == "slide"

    # Check slide 2 table content
    assert "Client Portfolio Risk Distribution" in doc.text
    assert "Taxpayer ID (SSN)" in doc.text
    assert "Robert Langdon" in doc.text
    assert "Eleanor Vance" in doc.text

    # Check slide 3 notes and body
    assert "Customer Support Escalation Protocols" in doc.text
    assert "--- Speaker Notes ---" in doc.text

    # Contractual invariant: page boundaries exactly slice into assembled text
    for page in doc.pages:
        sliced = doc.text[page.start:page.end]
        assert len(sliced) == page.char_count


def test_parse_clean_presentation_pptx():
    """Verify clean technical PPTX extracts properly with zero personal data."""
    path = FIXTURES_DIR / "12_clean_presentation.pptx"
    doc = extract_document(str(path))

    assert doc.extraction_status == "success"
    assert doc.source_type == "pptx"
    assert len(doc.pages) == 2
    assert "Cadence Enterprise Architecture" in doc.text
    assert "Microservice Tier Specifications" in doc.text


# ---------------------------------------------------------------------------
# 2. PDF (.pdf) Parsing Tests
# ---------------------------------------------------------------------------

def test_parse_wealth_management_digital_pdf():
    """Verify multi-page digital PDF extracts native text and page offsets."""
    path = FIXTURES_DIR / "13_wealth_management_portfolio.pdf"
    assert path.exists(), f"Missing fixture: {path}"

    doc = extract_document(str(path))
    assert doc.extraction_status == "success"
    assert doc.source_type == "pdf"
    assert len(doc.pages) == 2

    # Verify page 1 customer advisory text
    assert "Cadence Private Wealth Management" in doc.text
    assert "Jonathan K. Sampleton" in doc.text
    assert "Taxpayer Identification (SSN)" in doc.text

    # Verify page 2 compliance sign-off text
    assert "Regulatory Compliance & Risk Disclosure" in doc.text
    assert "Marcus Thorne" in doc.text

    # Contractual invariant: page boundary slicing
    for page in doc.pages:
        sliced = doc.text[page.start:page.end]
        assert len(sliced) == page.char_count


def test_parse_clean_whitepaper_pdf():
    """Verify clean multi-page technical whitepaper PDF parses cleanly."""
    path = FIXTURES_DIR / "14_clean_whitepaper.pdf"
    doc = extract_document(str(path))

    assert doc.extraction_status == "success"
    assert doc.source_type == "pdf"
    assert len(doc.pages) == 2
    assert "Cadence Financial AI Architecture Whitepaper" in doc.text
    assert "Formal Verification of State Transitions" in doc.text


@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="Tesseract OCR binary not found on system PATH")
def test_parse_scanned_pdf_memorandum():
    """Verify scanned image PDF is processed gracefully without crash."""
    path = FIXTURES_DIR / "15_scanned_id_memorandum.pdf"
    doc = extract_document(str(path))

    assert doc.source_type in ("pdf", "scanned_pdf")
    assert len(doc.pages) == 1
    # Either OCR succeeds or fallback records appropriate warnings
    assert doc.extraction_status in ("success", "partial", "failed")


# ---------------------------------------------------------------------------
# 3. Word (.docx) Parsing Tests
# ---------------------------------------------------------------------------

def test_parse_commercial_loan_agreement_docx():
    """Verify rich multi-section DOCX with borrower tables extracts sequential order."""
    path = FIXTURES_DIR / "16_commercial_loan_agreement.docx"
    assert path.exists(), f"Missing fixture: {path}"

    doc = extract_document(str(path))
    assert doc.extraction_status == "success"
    assert doc.source_type == "docx"
    assert len(doc.pages) == 1
    assert "Cadence Commercial Credit Agreement" in doc.text
    assert "Section 1: Borrower Information" in doc.text
    assert "Section 2: Guarantor Schedule" in doc.text
    assert "Apex Holding Group LLC" in doc.text


# ---------------------------------------------------------------------------
# 4. Encoded & International Text (.txt) Parsing Tests
# ---------------------------------------------------------------------------

def test_parse_utf8_bom_account_records():
    """Verify UTF-8 BOM signature is detected and stripped from body text."""
    path = FIXTURES_DIR / "17_utf8_bom_account_records.txt"
    doc = extract_document(str(path))

    assert doc.extraction_status == "success"
    assert doc.source_type == "txt"
    assert "Account Audit Records (UTF-8 BOM)" in doc.text
    assert not doc.text.startswith("\ufeff")


def test_parse_utf16le_payroll_export():
    """Verify UTF-16 LE encoded document with BOM extracts cleanly."""
    path = FIXTURES_DIR / "18_utf16_payroll_export.txt"
    doc = extract_document(str(path))

    assert doc.extraction_status == "success"
    assert doc.source_type == "txt"
    assert "Cadence Global Payroll Export" in doc.text
    assert "Risk Advisory" in doc.text


def test_parse_unicode_international_accents():
    """Verify multilingual text with French, German, and Japanese characters."""
    path = FIXTURES_DIR / "07_unicode_international.txt"
    doc = extract_document(str(path))

    assert doc.extraction_status == "success"
    assert "Hélène Synthétique" in doc.text
    assert "Johann Weiß" in doc.text
    assert "日本語のテスト" in doc.text


# ---------------------------------------------------------------------------
# 5. Security & Malformed Boundary Tests
# ---------------------------------------------------------------------------

def test_parse_corrupted_header_pdf_fails_closed():
    """Verify corrupt PDF header is safely rejected without raising exception."""
    path = FIXTURES_DIR / "19_corrupted_header.pdf"
    doc = extract_document(str(path))

    assert doc.extraction_status == "failed"
    assert len(doc.warnings) >= 1


def test_parse_renamed_executable_pptx_fails_closed():
    """Verify PE executable disguised as PPTX is blocked by signature sniffing."""
    path = FIXTURES_DIR / "20_renamed_executable.pptx"
    val = validate_file(str(path))

    assert val.is_valid is False
    assert val.error_code in ("ERR_RENAMED_EXECUTABLE", "ERR_DISGUISED_BINARY", "ERR_FORMAT_MISMATCH", "ERR_INVALID_FORMAT")

    doc = extract_document(str(path))
    assert doc.extraction_status == "failed"


def test_parse_empty_document_fails_closed():
    """Verify 0-byte file is rejected as fail-closed."""
    path = FIXTURES_DIR / "08_empty_document.txt"
    doc = extract_document(str(path))

    assert doc.extraction_status == "failed"
    assert any("ERR_EMPTY_FILE" in w.code or "ERR_VALIDATION_FAILED" in w.code for w in doc.warnings)


# ---------------------------------------------------------------------------
# 6. End-to-End Orchestration Pipeline Execution on All Document Formats
# ---------------------------------------------------------------------------

def test_pipeline_e2e_pptx_briefing(tmp_path):
    """End-to-end pipeline: PPTX presentation with PII is masked, verified, and released."""
    path = FIXTURES_DIR / "11_quarterly_briefing.pptx"
    trail = AuditTrail()
    art_mgr = ArtifactManager(storage_dir=tmp_path / "artifacts")

    result = process_document(str(path), audit_trail=trail, artifact_manager=art_mgr)

    assert result.workflow_status == "success"
    assert result.current_stage == PipelineStage.RELEASED
    assert result.release_allowed is True
    assert result.verification_status == "PASS"
    assert result.redactions_applied >= 3
    assert "EMAIL" in result.category_counts
    assert "PHONE" in result.category_counts
    assert "GOVERNMENT_ID" in result.category_counts


def test_pipeline_e2e_digital_pdf(tmp_path):
    """End-to-end pipeline: Digital PDF with PII is masked, verified, and released."""
    path = FIXTURES_DIR / "13_wealth_management_portfolio.pdf"
    trail = AuditTrail()
    art_mgr = ArtifactManager(storage_dir=tmp_path / "artifacts")

    result = process_document(str(path), audit_trail=trail, artifact_manager=art_mgr)

    assert result.workflow_status == "success"
    assert result.current_stage == PipelineStage.RELEASED
    assert result.release_allowed is True
    assert result.verification_status == "PASS"
    assert result.redactions_applied >= 3


def test_pipeline_e2e_commercial_loan_docx(tmp_path):
    """End-to-end pipeline: Rich DOCX with PII is masked, verified, and released."""
    path = FIXTURES_DIR / "16_commercial_loan_agreement.docx"
    trail = AuditTrail()
    art_mgr = ArtifactManager(storage_dir=tmp_path / "artifacts")

    result = process_document(str(path), audit_trail=trail, artifact_manager=art_mgr)

    assert result.workflow_status == "success"
    assert result.current_stage == PipelineStage.RELEASED
    assert result.release_allowed is True
    assert result.verification_status == "PASS"
    assert result.redactions_applied >= 3


def test_pipeline_e2e_utf8_bom(tmp_path):
    """End-to-end pipeline: UTF-8 BOM text file is masked, verified, and released."""
    path = FIXTURES_DIR / "17_utf8_bom_account_records.txt"
    trail = AuditTrail()
    art_mgr = ArtifactManager(storage_dir=tmp_path / "artifacts")

    result = process_document(str(path), audit_trail=trail, artifact_manager=art_mgr)

    assert result.workflow_status == "success"
    assert result.release_allowed is True
    assert result.verification_status == "PASS"


def test_pipeline_e2e_clean_documents_zero_leakage(tmp_path):
    """Clean PPTX and Clean PDF have zero PII detected and are released with 0 redactions."""
    art_mgr = ArtifactManager(storage_dir=tmp_path / "artifacts")

    res_pptx = process_document(str(FIXTURES_DIR / "12_clean_presentation.pptx"), artifact_manager=art_mgr)
    assert res_pptx.workflow_status == "success"
    assert res_pptx.release_allowed is True
    assert res_pptx.redactions_applied == 0

    res_pdf = process_document(str(FIXTURES_DIR / "14_clean_whitepaper.pdf"), artifact_manager=art_mgr)
    assert res_pdf.workflow_status == "success"
    assert res_pdf.release_allowed is True
    assert res_pdf.redactions_applied == 0
