"""Deterministic synthetic sample and fixture generator (Member 4 - Nancy).

PRIVACY & SAFETY POLICY:
1. ONLY clearly artificial / synthetic values are generated (e.g. example.com, 555-01xx).
2. NO real personal records, customer data, or live external APIs are queried.
3. Completely deterministic output given a seed value.
4. Independent from production processing; used strictly for demonstrations, testing, and evaluation.
"""

import os
import sys
import json
import random
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    import pptx
    from pptx.util import Inches, Pt
    HAS_PPTX = True
except ImportError:
    HAS_PPTX = False

try:
    import pymupdf
    HAS_PDF = True
except ImportError:
    try:
        import fitz as pymupdf
        HAS_PDF = True
    except ImportError:
        HAS_PDF = False

try:
    from PIL import Image, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

GENERATOR_VERSION = "1.0.0"

# Synthetic name pools (obviously artificial)
SYNTHETIC_FIRST_NAMES = ["Alex", "Morgan", "Taylor", "Jordan", "Casey", "Riley", "Avery", "Sam"]
SYNTHETIC_LAST_NAMES = ["Synthetic", "Testperson", "DemoUser", "Fictional", "Sampleton", "Mockford"]
SYNTHETIC_DOMAINS = ["example.com", "example.org", "testcorp.internal", "cadence-demo.test"]


class SyntheticSampleGenerator:
    """Deterministic generator for synthetic PII demonstration documents."""

    def __init__(self, seed: int = 42, output_dir: Optional[Path] = None):
        self.seed = seed
        self.rng = random.Random(seed)
        self.output_dir = Path(output_dir or Path(__file__).resolve().parent.parent / "demo_samples")
        self.fixtures_dir = self.output_dir / "fixtures"

    def _rand_email(self) -> str:
        first = self.rng.choice(SYNTHETIC_FIRST_NAMES).lower()
        last = self.rng.choice(SYNTHETIC_LAST_NAMES).lower()
        num = self.rng.randint(100, 999)
        dom = self.rng.choice(SYNTHETIC_DOMAINS)
        return f"{first}.{last}{num}@{dom}"

    def _rand_phone(self) -> str:
        # Standard reserved 555 exchange for fictional / test use
        line = self.rng.randint(100, 199)
        last4 = self.rng.randint(1000, 9999)
        return f"(555) 0{line:03d}-{last4:04d}"

    def _rand_ssn(self) -> str:
        # Fictional synthetic SSN adhering to area rules (not 000, 666, or 900+)
        area = self.rng.randint(100, 899)
        while area == 666:
            area = self.rng.randint(100, 899)
        mid = self.rng.randint(10, 99)
        end = self.rng.randint(1000, 9999)
        return f"{area:03d}-{mid:02d}-{end:04d}"

    def _rand_emp_id(self) -> str:
        num = self.rng.randint(10000, 99999)
        return f"CAD-EMP-{num}"

    def generate_all(self) -> Dict[str, Any]:
        """Generate all 10 synthetic scenarios and produce the manifest."""
        self.fixtures_dir.mkdir(parents=True, exist_ok=True)
        fixtures_meta: List[Dict[str, Any]] = []

        # 1. Scenario: Synthetic Email
        email_file = self.fixtures_dir / "01_synthetic_email.txt"
        e1, e2 = self._rand_email(), self._rand_email()
        email_file.write_text(
            f"Cadence Advisory Notification\n\n"
            f"Please send review submissions to project coordinator {e1}.\n"
            f"For automated escalations, copy {e2}.\n\n"
            f"Notice: This is a synthetic demonstration record.\n",
            encoding="utf-8"
        )
        fixtures_meta.append({
            "fixture_id": "synth-001",
            "scenario": "scenario_email",
            "file_type": "txt",
            "relative_path": "fixtures/01_synthetic_email.txt",
            "expected_categories": ["EMAIL"],
            "expected_entity_count": 2,
            "description": "Plain text document containing 2 synthetic email addresses.",
        })

        # 2. Scenario: Synthetic Phone
        phone_file = self.fixtures_dir / "02_synthetic_phone.txt"
        p1, p2 = self._rand_phone(), self._rand_phone()
        phone_file.write_text(
            f"Client Support Desk Roster\n\n"
            f"Primary hotline: {p1}\n"
            f"Backup branch dispatch: {p2}\n\n"
            f"Notice: Fictional telephone numbers using reserved 555 prefix.\n",
            encoding="utf-8"
        )
        fixtures_meta.append({
            "fixture_id": "synth-002",
            "scenario": "scenario_phone",
            "file_type": "txt",
            "relative_path": "fixtures/02_synthetic_phone.txt",
            "expected_categories": ["PHONE"],
            "expected_entity_count": 2,
            "description": "Plain text document containing 2 synthetic phone numbers.",
        })

        # 3. Scenario: Mixed PII
        mixed_file = self.fixtures_dir / "03_mixed_pii.txt"
        m_email = self._rand_email()
        m_phone = self._rand_phone()
        m_ssn = self._rand_ssn()
        m_emp = self._rand_emp_id()
        mixed_file.write_text(
            f"Employee Onboarding Summary\n\n"
            f"Employee ID: {m_emp}\n"
            f"Contact Email: {m_email}\n"
            f"Direct Line: {m_phone}\n"
            f"Taxpayer Identifier (Synthetic): {m_ssn}\n\n"
            f"Department: Synthetic Model Testing\n",
            encoding="utf-8"
        )
        fixtures_meta.append({
            "fixture_id": "synth-003",
            "scenario": "scenario_mixed_pii",
            "file_type": "txt",
            "relative_path": "fixtures/03_mixed_pii.txt",
            "expected_categories": ["EMPLOYEE_ID", "EMAIL", "PHONE", "GOVERNMENT_ID"],
            "expected_entity_count": 4,
            "description": "Multi-category plain text document with email, phone, government ID, and employee ID.",
        })

        # 4. Scenario: Clean Document Without PII
        clean_file = self.fixtures_dir / "04_clean_no_pii.txt"
        clean_file.write_text(
            f"Cadence Enterprise System Architecture Guidelines\n\n"
            f"1. Service Boundary Separation\n"
            f"All microservices must communicate exclusively via authenticated gRPC or mTLS REST endpoints.\n\n"
            f"2. Zero-Trust Access Policy\n"
            f"No public network routes may access persistent database backends directly.\n\n"
            f"3. Automated Audit Logging\n"
            f"All access control decisions must generate immutable telemetry records.\n",
            encoding="utf-8"
        )
        fixtures_meta.append({
            "fixture_id": "synth-004",
            "scenario": "scenario_clean_no_pii",
            "file_type": "txt",
            "relative_path": "fixtures/04_clean_no_pii.txt",
            "expected_categories": [],
            "expected_entity_count": 0,
            "description": "Benchmark clean technical document with zero personal identifiers.",
        })

        # 5. Scenario: Repeated Synthetic Entities
        rep_file = self.fixtures_dir / "05_repeated_entities.txt"
        rep_email = self._rand_email()
        rep_file.write_text(
            f"Cadence Vendor Compliance Circular\n\n"
            f"Section 1: Inquiries must be routed to {rep_email}.\n"
            f"Section 2: For billing audits, confirm receipt with {rep_email}.\n"
            f"Section 3: Security disclosures must cc {rep_email}.\n"
            f"Section 4: Technical escalations require sign-off from {rep_email}.\n",
            encoding="utf-8"
        )
        fixtures_meta.append({
            "fixture_id": "synth-005",
            "scenario": "scenario_repeated_entities",
            "file_type": "txt",
            "relative_path": "fixtures/05_repeated_entities.txt",
            "expected_categories": ["EMAIL"],
            "expected_entity_count": 4,
            "description": "Document featuring repeated occurrences of the same synthetic entity across paragraphs.",
        })

        # 6. Scenario: Multi-Category DOCX
        docx_file = self.fixtures_dir / "06_multi_category.docx"
        d_email = self._rand_email()
        d_phone = self._rand_phone()
        d_emp = self._rand_emp_id()
        if HAS_DOCX:
            doc = docx.Document()
            doc.add_heading("Cadence Vendor Risk Assessment", level=1)
            doc.add_paragraph("Confidential internal audit summary prepared for AI evaluation.")
            doc.add_paragraph(f"Auditor: {d_emp} | Contact: {d_email}")
            table = doc.add_table(rows=3, cols=3)
            hdr_cells = table.rows[0].cells
            hdr_cells[0].text = "Vendor Name"
            hdr_cells[1].text = "Security Lead"
            hdr_cells[2].text = "Emergency Telephone"
            r1 = table.rows[1].cells
            r1[0].text = "Apex Cloud Corp"
            r1[1].text = "Synthetic Contact A"
            r1[2].text = d_phone
            r2 = table.rows[2].cells
            r2[0].text = "Beacon Data Services"
            r2[1].text = "Synthetic Contact B"
            r2[2].text = "(555) 018-9944"
            doc.save(str(docx_file))
            fixtures_meta.append({
                "fixture_id": "synth-006",
                "scenario": "scenario_multi_category_docx",
                "file_type": "docx",
                "relative_path": "fixtures/06_multi_category.docx",
                "expected_categories": ["EMPLOYEE_ID", "EMAIL", "PHONE"],
                "expected_entity_count": 3,
                "description": "Word document (.docx) with structured tables and paragraphs containing synthetic PII.",
            })
        else:
            # Fallback if docx module unavailable
            docx_file.write_text(f"DOCX Fallback: Auditor {d_emp}, {d_email}, {d_phone}\n", encoding="utf-8")
            fixtures_meta.append({
                "fixture_id": "synth-006",
                "scenario": "scenario_multi_category_docx",
                "file_type": "txt",
                "relative_path": "fixtures/06_multi_category.docx",
                "expected_categories": ["EMPLOYEE_ID", "EMAIL", "PHONE"],
                "expected_entity_count": 3,
                "description": "Fallback text format for multi-category document.",
            })

        # 7. Scenario: Unicode International Characters
        unicode_file = self.fixtures_dir / "07_unicode_international.txt"
        u_email = "helene.test@modele-francais.example.com"
        u_email_de = "johann.beispiel@deutsche-bank-demo.example.org"
        unicode_file.write_text(
            f"Fiche de Conformité Européenne & Internationaler Bericht\n\n"
            f"Contact Paris: Hélène Synthétique ({u_email})\n"
            f"Prüfstelle Zürich: Johann Weiß ({u_email_de})\n"
            f"Téléphone Genève: +41 22 555 0199\n"
            f"日本語のテスト: 架空の顧客連絡先 (Tokyo branch: tokyo.synthetic@example.jp)\n\n"
            f"Remarque: Données entièrement fictives pour tests multilingues.\n",
            encoding="utf-8"
        )
        fixtures_meta.append({
            "fixture_id": "synth-007",
            "scenario": "scenario_unicode_international",
            "file_type": "txt",
            "relative_path": "fixtures/07_unicode_international.txt",
            "expected_categories": ["EMAIL", "PHONE"],
            "expected_entity_count": 4,
            "description": "Multilingual document with French, German, and Japanese characters and synthetic PII.",
        })

        # 8. Scenario: Empty Document (0-byte)
        empty_file = self.fixtures_dir / "08_empty_document.txt"
        empty_file.write_text("", encoding="utf-8")
        fixtures_meta.append({
            "fixture_id": "synth-008",
            "scenario": "scenario_empty",
            "file_type": "txt",
            "relative_path": "fixtures/08_empty_document.txt",
            "expected_categories": [],
            "expected_entity_count": 0,
            "description": "Zero-byte document used for testing fail-closed validation safeguards.",
        })

        # 9. Scenario: Long Document
        long_file = self.fixtures_dir / "09_long_document.txt"
        long_paragraphs = ["Cadence Financial Group Comprehensive Governance Overview\n"]
        for i in range(1, 21):
            if i % 5 == 0:
                p_text = f"Paragraph {i}: Audit checkpoint. Inquiries routed to checkpoint.{i}@{self._rand_email().split('@')[1]}."
            else:
                p_text = f"Paragraph {i}: Operational procedures continue under standard controls with no customer exceptions recorded."
            long_paragraphs.append(p_text)
        long_file.write_text("\n\n".join(long_paragraphs), encoding="utf-8")
        fixtures_meta.append({
            "fixture_id": "synth-009",
            "scenario": "scenario_long_document",
            "file_type": "txt",
            "relative_path": "fixtures/09_long_document.txt",
            "expected_categories": ["EMAIL"],
            "expected_entity_count": 4,
            "description": "Extended 20-paragraph document with sparse synthetic entities to test throughput and chunking.",
        })

        # 10. Scenario: Unsupported / Malformed Binary
        malformed_file = self.fixtures_dir / "10_malformed_binary.xyz"
        malformed_file.write_bytes(b"\x00\xFF\xFE\x00\xCA\xFE\xBA\xBE" * 16)
        fixtures_meta.append({
            "fixture_id": "synth-010",
            "scenario": "scenario_unsupported_malformed",
            "file_type": "xyz",
            "relative_path": "fixtures/10_malformed_binary.xyz",
            "expected_categories": [],
            "expected_entity_count": 0,
            "description": "Arbitrary unsupported binary file to verify input validation failure handling.",
        })

        # 11. Scenario: Presentation PPTX with Mixed PII
        pptx_file = self.fixtures_dir / "11_quarterly_briefing.pptx"
        p_advisor_email = self._rand_email()
        p_advisor_phone = self._rand_phone()
        p_client1_email = self._rand_email()
        p_client2_email = self._rand_email()
        p_ssn1 = self._rand_ssn()
        p_ssn2 = self._rand_ssn()
        p_hotline = self._rand_phone()
        p_notes_email = self._rand_email()

        if HAS_PPTX:
            prs = pptx.Presentation()
            
            # Slide 1: Title slide
            slide1 = prs.slides.add_slide(prs.slide_layouts[0])
            slide1.shapes.title.text = "Cadence Financial Group - Quarterly Client Briefing"
            subtitle1 = slide1.placeholders[1]
            subtitle1.text = f"Prepared by Wealth Advisory Lead: {p_advisor_email}\nDirect Phone: {p_advisor_phone}"

            # Slide 2: Table slide
            slide2 = prs.slides.add_slide(prs.slide_layouts[6])
            tb2 = slide2.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(8.4), Inches(0.8))
            tb2.text_frame.text = "Client Portfolio Risk Distribution"

            table_shape = slide2.shapes.add_table(3, 3, Inches(0.8), Inches(1.6), Inches(8.4), Inches(2.2))
            tbl = table_shape.table
            tbl.cell(0, 0).text = "Client Name"
            tbl.cell(0, 1).text = "Taxpayer ID (SSN)"
            tbl.cell(0, 2).text = "Contact Email"

            tbl.cell(1, 0).text = "Robert Langdon"
            tbl.cell(1, 1).text = p_ssn1
            tbl.cell(1, 2).text = p_client1_email

            tbl.cell(2, 0).text = "Eleanor Vance"
            tbl.cell(2, 1).text = p_ssn2
            tbl.cell(2, 2).text = p_client2_email

            # Slide 3: Escalation and Speaker Notes
            slide3 = prs.slides.add_slide(prs.slide_layouts[6])
            tb3 = slide3.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(8.4), Inches(0.8))
            tb3.text_frame.text = "Customer Support Escalation Protocols"

            tb3_body = slide3.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(8.4), Inches(3.0))
            tb3_body.text_frame.text = (
                f"All urgent customer complaints must follow Cadence incident resolution workflows.\n"
                f"Emergency dispatch hotline: {p_hotline}"
            )

            slide3.notes_slide.notes_text_frame.text = (
                f"Confidential Notes: For unresolved tickets, notify advisor at {p_notes_email}."
            )

            prs.save(str(pptx_file))
            fixtures_meta.append({
                "fixture_id": "synth-011",
                "scenario": "scenario_pptx_presentation",
                "file_type": "pptx",
                "relative_path": "fixtures/11_quarterly_briefing.pptx",
                "expected_categories": ["EMAIL", "PHONE", "GOVERNMENT_ID"],
                "expected_entity_count": 6,
                "description": "PowerPoint presentation (.pptx) with slides, tables, and speaker notes containing synthetic PII.",
            })
        else:
            pptx_file.write_text(f"PPTX Fallback: Advisor {p_advisor_email}, Phone {p_advisor_phone}, SSN {p_ssn1}\n", encoding="utf-8")
            fixtures_meta.append({
                "fixture_id": "synth-011",
                "scenario": "scenario_pptx_presentation",
                "file_type": "txt",
                "relative_path": "fixtures/11_quarterly_briefing.pptx",
                "expected_categories": ["EMAIL", "PHONE", "GOVERNMENT_ID"],
                "expected_entity_count": 3,
                "description": "Fallback text format for PPTX scenario.",
            })

        # 12. Scenario: Clean Presentation Without PII
        clean_pptx_file = self.fixtures_dir / "12_clean_presentation.pptx"
        if HAS_PPTX:
            prs_clean = pptx.Presentation()
            s1 = prs_clean.slides.add_slide(prs_clean.slide_layouts[0])
            s1.shapes.title.text = "Cadence Enterprise Architecture & Cloud Migration"
            s1.placeholders[1].text = "Technical Blueprint - High Availability & Distributed Services"

            s2 = prs_clean.slides.add_slide(prs_clean.slide_layouts[6])
            tb_clean = s2.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(8.4), Inches(0.8))
            tb_clean.text_frame.text = "Microservice Tier Specifications"
            tb_body = s2.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(8.4), Inches(3.0))
            tb_body.text_frame.text = (
                "All ingestion microservices execute in sandboxed ephemeral containers.\n"
                "Inter-service communication is authenticated with mutual TLS (mTLS).\n"
                "Zero personal identifiers are processed on public gateways."
            )

            prs_clean.save(str(clean_pptx_file))
            fixtures_meta.append({
                "fixture_id": "synth-012",
                "scenario": "scenario_pptx_clean",
                "file_type": "pptx",
                "relative_path": "fixtures/12_clean_presentation.pptx",
                "expected_categories": [],
                "expected_entity_count": 0,
                "description": "Clean presentation (.pptx) with zero personal identifiers.",
            })
        else:
            clean_pptx_file.write_text("Clean presentation architecture\n", encoding="utf-8")
            fixtures_meta.append({
                "fixture_id": "synth-012",
                "scenario": "scenario_pptx_clean",
                "file_type": "txt",
                "relative_path": "fixtures/12_clean_presentation.pptx",
                "expected_categories": [],
                "expected_entity_count": 0,
                "description": "Clean presentation fallback text.",
            })

        # 13. Scenario: Multi-Page Digital PDF with PII
        pdf_file = self.fixtures_dir / "13_wealth_management_portfolio.pdf"
        pdf_client_email = self._rand_email()
        pdf_client_phone = self._rand_phone()
        pdf_client_ssn = self._rand_ssn()
        pdf_officer_email = self._rand_email()
        pdf_officer_phone = self._rand_phone()

        if HAS_PDF:
            doc = pymupdf.open()
            
            # Page 1
            page1 = doc.new_page(width=595, height=842)
            p1_text = (
                "Cadence Private Wealth Management - Portfolio Statement\n\n"
                "CONFIDENTIAL CLIENT ADVISORY SUMMARY\n\n"
                "Client Information\n"
                "Full Name: Jonathan K. Sampleton\n"
                f"Taxpayer Identification (SSN): {pdf_client_ssn}\n"
                f"Primary Email: {pdf_client_email}\n"
                f"Telephone Contact: {pdf_client_phone}\n\n"
                "Account Overview\n"
                "Account Number: CAD-WM-882194\n"
                "Custodian: Cadence Trust Bank N.A.\n"
                "Portfolio Strategy: Capital Appreciation & Risk Hedging\n"
            )
            page1.insert_text((50, 72), p1_text, fontsize=11)

            # Page 2
            page2 = doc.new_page(width=595, height=842)
            p2_text = (
                "Regulatory Compliance & Risk Disclosure\n\n"
                "This portfolio statement complies with SEC and FINRA disclosure requirements.\n"
                "Audited under Cadence Financial Group compliance standards.\n\n"
                "Compliance Sign-off\n"
                "Supervising Principal: Marcus Thorne\n"
                f"Compliance Email: {pdf_officer_email}\n"
                f"Direct Verification Line: {pdf_officer_phone}\n\n"
                "Notice: All figures and identifiers are synthetic test data.\n"
            )
            page2.insert_text((50, 72), p2_text, fontsize=11)

            doc.save(str(pdf_file))
            doc.close()
            fixtures_meta.append({
                "fixture_id": "synth-013",
                "scenario": "scenario_pdf_document",
                "file_type": "pdf",
                "relative_path": "fixtures/13_wealth_management_portfolio.pdf",
                "expected_categories": ["EMAIL", "PHONE", "GOVERNMENT_ID"],
                "expected_entity_count": 5,
                "description": "Multi-page digital PDF (.pdf) with client records, SSN, emails, and telephone numbers.",
            })
        else:
            pdf_file.write_text(f"PDF Fallback: {pdf_client_email}, {pdf_client_phone}, {pdf_client_ssn}\n", encoding="utf-8")
            fixtures_meta.append({
                "fixture_id": "synth-013",
                "scenario": "scenario_pdf_document",
                "file_type": "txt",
                "relative_path": "fixtures/13_wealth_management_portfolio.pdf",
                "expected_categories": ["EMAIL", "PHONE", "GOVERNMENT_ID"],
                "expected_entity_count": 3,
                "description": "Fallback text format for PDF scenario.",
            })

        # 14. Scenario: Clean Digital PDF Without PII
        clean_pdf_file = self.fixtures_dir / "14_clean_whitepaper.pdf"
        if HAS_PDF:
            doc_clean = pymupdf.open()
            cp1 = doc_clean.new_page(width=595, height=842)
            cp1.insert_text(
                (50, 72),
                "Cadence Financial AI Architecture Whitepaper\n\n"
                "Executive Summary\n"
                "This technical paper presents the mathematical foundations of our zero-leakage redaction pipeline.\n"
                "The design ensures deterministic guarantees across all ingested media formats.\n\n"
                "Core Principles:\n"
                "1. Zero false negatives through defense-in-depth detection.\n"
                "2. Reversible tokenization with AES-GCM-256 cryptographic isolation.\n"
                "3. Automated audit logging of all transformation operations.\n",
                fontsize=11,
            )
            cp2 = doc_clean.new_page(width=595, height=842)
            cp2.insert_text(
                (50, 72),
                "Section 2: Formal Verification of State Transitions\n\n"
                "State machine transitions obey strict monotonic invariance.\n"
                "Any failed verification immediately aborts the release pipeline under fail-closed policies.\n",
                fontsize=11,
            )
            doc_clean.save(str(clean_pdf_file))
            doc_clean.close()
            fixtures_meta.append({
                "fixture_id": "synth-014",
                "scenario": "scenario_pdf_clean",
                "file_type": "pdf",
                "relative_path": "fixtures/14_clean_whitepaper.pdf",
                "expected_categories": [],
                "expected_entity_count": 0,
                "description": "Clean multi-page PDF (.pdf) with zero personal identifiers.",
            })
        else:
            clean_pdf_file.write_text("Clean PDF whitepaper\n", encoding="utf-8")
            fixtures_meta.append({
                "fixture_id": "synth-014",
                "scenario": "scenario_pdf_clean",
                "file_type": "txt",
                "relative_path": "fixtures/14_clean_whitepaper.pdf",
                "expected_categories": [],
                "expected_entity_count": 0,
                "description": "Clean PDF fallback text.",
            })

        # 15. Scenario: Scanned PDF Attachment
        scanned_pdf_file = self.fixtures_dir / "15_scanned_id_memorandum.pdf"
        scan_phone = "(555) 011-4455"
        if HAS_PDF and HAS_PIL:
            img = Image.new("RGB", (800, 1000), color=(255, 255, 255))
            draw = ImageDraw.Draw(img)
            draw.text(
                (50, 60),
                "CADENCE OPERATIONS MEMORANDUM\n\n"
                "Scanned Verification Slip\n"
                "Employee ID: CAD-EMP-77129\n"
                f"Support Desk Phone: {scan_phone}\n"
                "Authorization Status: APPROVED\n\n"
                "Notice: Rasterized synthetic scan.\n",
                fill=(0, 0, 0),
            )
            temp_img = self.fixtures_dir / "temp_scan.png"
            img.save(str(temp_img))

            doc_scan = pymupdf.open()
            sp = doc_scan.new_page(width=img.width, height=img.height)
            sp.insert_image(sp.rect, filename=str(temp_img))
            doc_scan.save(str(scanned_pdf_file))
            doc_scan.close()
            if temp_img.exists():
                temp_img.unlink()

            fixtures_meta.append({
                "fixture_id": "synth-015",
                "scenario": "scenario_pdf_scanned",
                "file_type": "pdf",
                "relative_path": "fixtures/15_scanned_id_memorandum.pdf",
                "expected_categories": ["EMPLOYEE_ID", "PHONE"],
                "expected_entity_count": 2,
                "description": "Image-only scanned PDF (.pdf) verifying OCR and image fallback handling.",
            })
        else:
            scanned_pdf_file.write_text(f"Scanned fallback: CAD-EMP-77129, {scan_phone}\n", encoding="utf-8")
            fixtures_meta.append({
                "fixture_id": "synth-015",
                "scenario": "scenario_pdf_scanned",
                "file_type": "txt",
                "relative_path": "fixtures/15_scanned_id_memorandum.pdf",
                "expected_categories": ["EMPLOYEE_ID", "PHONE"],
                "expected_entity_count": 2,
                "description": "Scanned fallback text.",
            })

        # 16. Scenario: Rich Commercial Loan DOCX
        loan_docx_file = self.fixtures_dir / "16_commercial_loan_agreement.docx"
        l_borrower_email = self._rand_email()
        l_borrower_phone = self._rand_phone()
        l_borrower_ssn = self._rand_ssn()
        l_guarantor_email = self._rand_email()
        l_guarantor_phone = self._rand_phone()

        if HAS_DOCX:
            doc_loan = docx.Document()
            doc_loan.add_heading("Cadence Commercial Credit Agreement", level=1)
            doc_loan.add_paragraph("Master Facility Loan Document - Confidential Execution Copy")
            
            doc_loan.add_heading("Section 1: Borrower Information", level=2)
            doc_loan.add_paragraph(
                f"Primary Borrower: Jonathan M. Mockford\n"
                f"Taxpayer Identification (SSN): {l_borrower_ssn}\n"
                f"Official Communication Email: {l_borrower_email}\n"
                f"Telephone Number: {l_borrower_phone}"
            )

            doc_loan.add_heading("Section 2: Guarantor Schedule", level=2)
            table_loan = doc_loan.add_table(rows=2, cols=3)
            t_hdr = table_loan.rows[0].cells
            t_hdr[0].text = "Guarantor Name"
            t_hdr[1].text = "Designated Email"
            t_hdr[2].text = "Emergency Telephone"

            t_row1 = table_loan.rows[1].cells
            t_row1[0].text = "Apex Holding Group LLC"
            t_row1[1].text = l_guarantor_email
            t_row1[2].text = l_guarantor_phone

            doc_loan.save(str(loan_docx_file))
            fixtures_meta.append({
                "fixture_id": "synth-016",
                "scenario": "scenario_docx_loan_agreement",
                "file_type": "docx",
                "relative_path": "fixtures/16_commercial_loan_agreement.docx",
                "expected_categories": ["EMAIL", "PHONE", "GOVERNMENT_ID"],
                "expected_entity_count": 5,
                "description": "Multi-section Word document (.docx) with structured borrower tables, SSN, and contacts.",
            })
        else:
            loan_docx_file.write_text(f"DOCX Loan fallback: {l_borrower_ssn}, {l_borrower_email}, {l_borrower_phone}\n", encoding="utf-8")
            fixtures_meta.append({
                "fixture_id": "synth-016",
                "scenario": "scenario_docx_loan_agreement",
                "file_type": "txt",
                "relative_path": "fixtures/16_commercial_loan_agreement.docx",
                "expected_categories": ["EMAIL", "PHONE", "GOVERNMENT_ID"],
                "expected_entity_count": 3,
                "description": "DOCX Loan fallback text.",
            })

        # 17. Scenario: UTF-8 with BOM Encoded Text
        bom_file = self.fixtures_dir / "17_utf8_bom_account_records.txt"
        bom_email = self._rand_email()
        bom_phone = self._rand_phone()
        bom_text = (
            "Account Audit Records (UTF-8 BOM)\n\n"
            f"Customer Contact: {bom_email}\n"
            f"Escalation Phone: {bom_phone}\n"
            "Status: Validated\n"
        )
        bom_bytes = b"\xef\xbb\xbf" + bom_text.encode("utf-8")
        bom_file.write_bytes(bom_bytes)
        fixtures_meta.append({
            "fixture_id": "synth-017",
            "scenario": "scenario_utf8_bom",
            "file_type": "txt",
            "relative_path": "fixtures/17_utf8_bom_account_records.txt",
            "expected_categories": ["EMAIL", "PHONE"],
            "expected_entity_count": 2,
            "description": "Plain text document encoded in UTF-8 with Byte Order Mark (BOM) containing synthetic PII.",
        })

        # 18. Scenario: UTF-16 LE Encoded Text
        utf16_file = self.fixtures_dir / "18_utf16_payroll_export.txt"
        u16_email = self._rand_email()
        u16_ssn = self._rand_ssn()
        u16_text = (
            "Cadence Global Payroll Export (UTF-16 LE)\n\n"
            f"Employee Email: {u16_email}\n"
            f"Employee SSN: {u16_ssn}\n"
            "Department: Risk Advisory\n"
        )
        utf16_file.write_bytes(u16_text.encode("utf-16"))
        fixtures_meta.append({
            "fixture_id": "synth-018",
            "scenario": "scenario_utf16_payroll",
            "file_type": "txt",
            "relative_path": "fixtures/18_utf16_payroll_export.txt",
            "expected_categories": ["EMAIL", "GOVERNMENT_ID"],
            "expected_entity_count": 2,
            "description": "Plain text export encoded in UTF-16 LE with BOM containing synthetic SSN and email.",
        })

        # 19. Scenario: Corrupted PDF Header (Security Boundary)
        corrupt_file = self.fixtures_dir / "19_corrupted_header.pdf"
        corrupt_file.write_bytes(b"%PDF-1.7\nCorrupted header content \x00\xff << stream broken >>")
        fixtures_meta.append({
            "fixture_id": "synth-019",
            "scenario": "scenario_corrupted_pdf",
            "file_type": "pdf",
            "relative_path": "fixtures/19_corrupted_header.pdf",
            "expected_categories": [],
            "expected_entity_count": 0,
            "description": "Malformed corrupted PDF header testing fail-closed error handling.",
        })

        # 20. Scenario: Renamed Windows Executable as PPTX (Security Boundary)
        renamed_exe_file = self.fixtures_dir / "20_renamed_executable.pptx"
        pe_bytes = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00This program cannot be run in DOS mode."
        renamed_exe_file.write_bytes(pe_bytes)
        fixtures_meta.append({
            "fixture_id": "synth-020",
            "scenario": "scenario_renamed_executable_pptx",
            "file_type": "pptx",
            "relative_path": "fixtures/20_renamed_executable.pptx",
            "expected_categories": [],
            "expected_entity_count": 0,
            "description": "Malicious Windows PE executable disguised with .pptx extension to test format sniffing rejection.",
        })

        # Assemble and write manifest
        manifest_data = {
            "generator_version": GENERATOR_VERSION,
            "seed": self.seed,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "fixture_count": len(fixtures_meta),
            "privacy_notice": (
                "All fixtures are 100% synthetically generated for Cadence AI Governance case study demonstration. "
                "No real personal records, customer data, or live identifiers are contained."
            ),
            "fixtures": fixtures_meta,
        }

        manifest_path = self.output_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        return manifest_data


def main():
    parser = argparse.ArgumentParser(description="Deterministic Synthetic PII Fixture Generator (Nancy - Member 4)")
    parser.add_argument("--seed", type=int, default=42, help="Integer random seed for determinism (default: 42)")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory path (default: demo_samples)")
    parser.add_argument("--manifest", type=str, default=None, help="Manifest output path (default: demo_samples/manifest.json)")
    args = parser.parse_args()

    out_dir = Path(args.output_dir) if args.output_dir else None
    generator = SyntheticSampleGenerator(seed=args.seed, output_dir=out_dir)
    manifest = generator.generate_all()

    print(f"[OK] Successfully generated {manifest['fixture_count']} synthetic demonstration fixtures.")
    print(f"[OK] Manifest written to: {generator.output_dir / 'manifest.json'}")
    print(f"[OK] Generator seed: {manifest['seed']}")


if __name__ == "__main__":
    main()
