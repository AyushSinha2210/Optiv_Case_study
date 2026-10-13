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
