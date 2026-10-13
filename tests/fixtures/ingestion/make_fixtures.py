"""Deterministic generator for synthetic test fixtures.

Creates small, hermetic fixtures covering normal documents, scanned/rotated pages,
corrupt artifacts, security attacks (zip bombs, renamed binaries), and encodings.
"""

import os
import zipfile
import zlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FIXTURES_DIR = Path(__file__).parent


def create_clean_text_pdf(output_path: Path):
    """Generate a clean 2-page digital PDF with headings and tables using PyMuPDF."""
    import pymupdf
    doc = pymupdf.open()

    # Page 1
    page1 = doc.new_page(width=595, height=842)
    p1_text = (
        "Cadence Financial Group - Annual Risk Review\n\n"
        "Executive Summary\n"
        "This report outlines third-party risk management assessments for fiscal year 2026.\n\n"
        "Vendor Assessment Matrix\n"
        "Vendor Name | Tier | Risk Score\n"
        "Apex Systems | Tier 1 | High\n"
        "Beacon Data | Tier 2 | Moderate\n"
    )
    page1.insert_text((50, 72), p1_text, fontsize=12)

    # Page 2
    page2 = doc.new_page(width=595, height=842)
    p2_text = (
        "Compliance Sign-off\n\n"
        "Reviewed and approved by Operations Risk Committee.\n"
        "Audit Lead: Samantha Vance\n"
        "Contact: svance@cadencefg.com\n"
    )
    page2.insert_text((50, 72), p2_text, fontsize=12)

    doc.save(str(output_path))
    doc.close()


def create_scanned_pdf(output_path: Path, rotate_angle: int = 0):
    """Render synthetic text onto a raster image and embed into a 1-page PDF."""
    img = Image.new("RGB", (800, 1100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text(
        (60, 80),
        "CONFIDENTIAL MEMORANDUM\n\n"
        "Account Authorization Form\n"
        "Employee: Julian Thorne\n"
        "Employee ID: CAD-77129\n"
        "Department: Investment Banking\n"
        "Approved Amount: $250,000\n",
        fill=(0, 0, 0),
    )

    if rotate_angle != 0:
        img = img.rotate(rotate_angle, expand=True)

    img_bytes_path = output_path.with_suffix(".png")
    img.save(str(img_bytes_path))

    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page(width=img.width, height=img.height)
    page.insert_image(page.rect, filename=str(img_bytes_path))
    doc.save(str(output_path))
    doc.close()

    if img_bytes_path.exists():
        img_bytes_path.unlink()


def create_mixed_pdf(output_path: Path):
    """Create a 2-page PDF: Page 1 is native digital text, Page 2 is a scanned image."""
    import pymupdf
    doc = pymupdf.open()

    # Page 1: Digital text
    page1 = doc.new_page(width=595, height=842)
    page1.insert_text(
        (50, 72),
        "Section 1: Governance Framework\n\nAll employees must abide by Cadence data privacy controls.\n",
        fontsize=12,
    )

    # Page 2: Scanned image
    img = Image.new("RGB", (600, 800), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((40, 50), "Scanned Attachment\nReceipt Ref: RC-99201\nVerified By: Operations", fill=(0, 0, 0))
    img_temp = output_path.with_name("temp_mixed.png")
    img.save(str(img_temp))

    page2 = doc.new_page(width=600, height=800)
    page2.insert_image(page2.rect, filename=str(img_temp))

    doc.save(str(output_path))
    doc.close()
    if img_temp.exists():
        img_temp.unlink()


def create_sample_docx(output_path: Path):
    """Create a DOCX with header, footer, interleaved paragraphs, and tables."""
    import docx
    doc = docx.Document()

    # Header and Footer
    section = doc.sections[0]
    section.header.paragraphs[0].text = "Cadence Internal Controls - Policy Document"
    section.footer.paragraphs[0].text = "Page 1 | Confidential"

    # Headings and paragraphs
    doc.add_heading("Third-Party Data Handling Policy", level=1)
    doc.add_paragraph("Employees are strictly forbidden from sharing customer PII with unverified vendors.")

    # Interleaved Table
    table = doc.add_table(rows=3, cols=3)
    headers = ["Service Category", "Risk Level", "Mandatory Safeguard"]
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h

    row1 = ["Cloud Storage", "High", "KMS Encryption"]
    for i, val in enumerate(row1):
        table.rows[1].cells[i].text = val

    row2 = ["Email Relay", "Medium", "TLS 1.3"]
    for i, val in enumerate(row2):
        table.rows[2].cells[i].text = val

    # Subsequent paragraph
    doc.add_paragraph("Exceptions must be approved by the Chief Information Security Officer.")

    doc.save(str(output_path))


def create_sample_pptx(output_path: Path):
    """Create a PPTX with title, shapes, table, and speaker notes."""
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.enum.shapes import MSO_SHAPE

    prs = Presentation()
    slide_layout = prs.slide_layouts[0]  # Title slide
    slide = prs.slides.add_slide(slide_layout)

    # Title & Subtitle
    slide.shapes.title.text = "Cadence Financial Group TPRM Briefing"
    subtitle = slide.placeholders[1]
    subtitle.text = "Quarterly Compliance & Cyber Review"

    # Slide 2: Table and speaker notes
    slide_layout2 = prs.slide_layouts[6]  # Blank slide
    slide2 = prs.slides.add_slide(slide_layout2)

    # Title box
    tb = slide2.shapes.add_textbox(Inches(1), Inches(0.5), Inches(8), Inches(1))
    tb.text_frame.text = "Vendor Risk Distribution"

    # Table shape
    rows, cols = 3, 2
    table_shape = slide2.shapes.add_table(rows, cols, Inches(1), Inches(2), Inches(6), Inches(2))
    table = table_shape.table
    table.cell(0, 0).text = "Vendor"
    table.cell(0, 1).text = "Status"
    table.cell(1, 0).text = "Apex Systems"
    table.cell(1, 1).text = "Audited"
    table.cell(2, 0).text = "Beacon Data"
    table.cell(2, 1).text = "Pending"

    # Speaker notes
    notes_slide = slide2.notes_slide
    notes_slide.notes_text_frame.text = "Highlight to the board that Apex audit is completed without findings."

    prs.save(str(output_path))


def create_txt_files(utf8_path: Path, latin1_path: Path):
    """Generate sample UTF-8 and Latin-1 encoded plain text files."""
    utf8_path.write_text(
        "Cadence Audit Notes\nDate: 2026-10-11\nAuthor: René Descartes\nStatus: Verified\n",
        encoding="utf-8",
    )
    latin1_path.write_bytes(
        "Cadence Regional Report\nBranch: Zürich\nDirector: François Mitterrand\n".encode("latin-1")
    )


def create_corrupt_file(output_path: Path):
    """Generate a file with corrupted header and body bytes."""
    output_path.write_bytes(b"%PDF-1.7\nCorrupt trailer and broken catalog dictionary <<\x00\xff")


def create_renamed_executable(output_path: Path):
    """Create a Windows PE binary header renamed as .pdf."""
    # MZ executable stub
    pe_bytes = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00This program cannot be run in DOS mode."
    output_path.write_bytes(pe_bytes)


def create_encrypted_pdf(output_path: Path):
    """Create a password-protected encrypted PDF using PyMuPDF."""
    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Confidential Encrypted Content")
    doc.save(
        str(output_path),
        encryption=pymupdf.PDF_ENCRYPT_AES_256,
        user_pw="secret123",
        owner_pw="admin123",
    )
    doc.close()


def create_zip_bomb_docx(output_path: Path):
    """Create a safe synthetic high-compression zip bomb artifact simulating a DOCX."""
    # Create 15 MB of repeating zeros compressed down to a few kilobytes
    zero_bytes = b"0" * (15 * 1024 * 1024)
    with zipfile.ZipFile(str(output_path), "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", b"<Types></Types>")
        zf.writestr("word/document.xml", zero_bytes)


def generate_all_fixtures():
    """Generate all deterministic fixtures in tests/fixtures/ingestion."""
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    create_clean_text_pdf(FIXTURES_DIR / "clean_text.pdf")
    create_scanned_pdf(FIXTURES_DIR / "scanned_page.pdf")
    create_scanned_pdf(FIXTURES_DIR / "rotated_scanned.pdf", rotate_angle=90)
    create_mixed_pdf(FIXTURES_DIR / "mixed.pdf")
    create_sample_docx(FIXTURES_DIR / "sample.docx")
    create_sample_pptx(FIXTURES_DIR / "sample.pptx")
    create_txt_files(FIXTURES_DIR / "utf8.txt", FIXTURES_DIR / "latin1.txt")
    (FIXTURES_DIR / "empty.txt").write_bytes(b"")
    create_corrupt_file(FIXTURES_DIR / "corrupt.pdf")
    create_renamed_executable(FIXTURES_DIR / "renamed_exe.pdf")
    create_encrypted_pdf(FIXTURES_DIR / "encrypted.pdf")
    create_zip_bomb_docx(FIXTURES_DIR / "zip_bomb.docx")
    print(f"All synthetic fixtures successfully created in {FIXTURES_DIR}")


if __name__ == "__main__":
    generate_all_fixtures()
