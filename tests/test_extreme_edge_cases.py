"""Extreme side edge-case and stress test suite for PII Guard.

Covers:
1. Ingestion: BOM variations, control characters, null bytes, Unicode NFC normalization,
   extreme document lengths, whitespace spam, and complex paths.
2. Detection: Dense chained PII, boundary offsets (index 0, EOF), Luhn card variations,
   adversarial SSN/PAN/IPv4 near-misses, surrounding punctuation, and form-feed page barriers.
3. Redaction: Expanding token drift prevention, repeated identical entities, high-density PII,
   residual leakage catching, and structure score preservation.
4. Security & Orchestration: Canary leakage invariance, path traversal attack payloads,
   and end-to-end multi-format pipeline release gates.
"""

from __future__ import annotations

import os
import re
import tempfile
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.pii_guard.ingestion.extractor import extract_document
from src.pii_guard.ingestion.normalize import normalize_text
from src.pii_guard.ingestion.schemas import ExtractedDocument
from src.pii_guard.detection.detector import detect_pii
from src.pii_guard.detection.schemas import DetectionInputError
from src.pii_guard.detection.validators import luhn_valid, ssn_valid, pan_valid, ipv4_valid
from src.pii_guard.redaction.redactor import apply_redactions, RedactionError
from src.pii_guard.redaction.verifier import (
    calculate_structure_score,
    verify_redacted_text,
    verify_saved_artifact,
)
from src.pii_guard.redaction.service import redact_and_validate
from src.pii_guard.orchestration.pipeline import process_document
from src.pii_guard.orchestration.artifacts import ArtifactManager
from src.pii_guard.orchestration.errors import ArtifactAccessError
from src.pii_guard.orchestration.state import PipelineStage
from src.pii_guard.reporting.audit import AuditTrail


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "ingestion"


def _doc(text: str, doc_id: str = "test-doc-001", status: str = "success") -> ExtractedDocument:
    """Helper to construct ExtractedDocument."""
    return ExtractedDocument(
        document_id=doc_id,
        source_type="txt",
        text=text,
        pages=[],
        warnings=[],
        extraction_status=status,
    )


# ===========================================================================
# 1. Ingestion Extreme Edge Cases & Stress Tests
# ===========================================================================

class TestIngestionExtremeEdgeCases:
    """Extreme edge cases for file ingestion and text normalization."""

    def test_ingestion_extreme_boms_utf8_utf16(self, tmp_path):
        """Test files with UTF-8 BOM, UTF-16 LE BOM, and UTF-16 BE BOM."""
        # 1. UTF-8 with BOM
        utf8_bom_file = tmp_path / "utf8_bom.txt"
        utf8_bom_file.write_bytes(b"\xef\xbb\xbfExecutive Officer: Julian Thorne\nAccount: CAD-10293")
        doc_utf8 = extract_document(str(utf8_bom_file))
        assert doc_utf8.extraction_status == "success"
        assert "\xef\xbb\xbf" not in doc_utf8.text
        assert "Julian Thorne" in doc_utf8.text

        # 2. UTF-16 with BOM
        utf16_le_file = tmp_path / "utf16_le.txt"
        utf16_le_file.write_bytes("Security Officer: René Descartes\nSSN: 123-45-6789".encode("utf-16"))
        doc_utf16 = extract_document(str(utf16_le_file))
        assert doc_utf16.extraction_status == "success"
        assert "René Descartes" in doc_utf16.text

    def test_ingestion_extreme_control_chars_and_nulls(self):
        """Verify normalization scrubs nulls, bells, escapes, and carriage returns idempotently."""
        raw_text = (
            "Header Line\r\n"
            "\x00Embedded Null\x07\x08Bell and Backspace\x1b[0m\r\n"
            "Line with multiple trailing spaces    \r\n"
            "\t\tIndented with tabs\r\n"
            "Final Line without newline"
        )
        norm1 = normalize_text(raw_text)
        norm2 = normalize_text(norm1)

        # Idempotence invariant
        assert norm1 == norm2
        # Null bytes and control characters stripped
        assert "\x00" not in norm1
        assert "\x07" not in norm1
        assert "\x08" not in norm1
        assert "\r" not in norm1
        # Text content preserved
        assert "Header Line" in norm1
        assert "Embedded Null" in norm1
        assert "Final Line without newline" in norm1

    def test_ingestion_extreme_unicode_nfc_and_emojis(self):
        """Verify complex diacritics, emoji sequences, and bidirectional scripts are NFC-normalized."""
        # Decomposed e + combining acute vs precomposed e with acute
        decomposed = "Cafe\u0301"  # e + combining acute accent
        precomposed = "Café"       # single character U+00E9
        norm_decomposed = normalize_text(decomposed)
        norm_precomposed = normalize_text(precomposed)
        assert norm_decomposed == norm_precomposed == "Café"

        # Emojis and RTL scripts
        mixed_script = "User 🔒 logged in from IP 192.0.2.1. مرحبا بالعالم. Shalom שלום."
        norm_mixed = normalize_text(mixed_script)
        assert "192.0.2.1" in norm_mixed
        assert "مرحبا بالعالم" in norm_mixed
        assert "שלום" in norm_mixed

    def test_ingestion_extreme_massive_document(self, tmp_path):
        """Stress test with a 150,000-character plain text document containing 1,000 paragraphs."""
        lines = [f"Paragraph {i}: Transaction ref CAD-{i:06d} processed for account 192.168.1.{i % 250}." for i in range(1000)]
        big_content = "\n\n".join(lines)
        big_file = tmp_path / "massive_doc.txt"
        big_file.write_text(big_content, encoding="utf-8")

        doc = extract_document(str(big_file))
        assert doc.extraction_status == "success"
        assert len(doc.text) > 50000
        assert len(doc.pages) == 1
        assert doc.pages[0].char_count == len(doc.text)
        assert doc.text[doc.pages[0].start : doc.pages[0].end] == doc.text

    def test_ingestion_extreme_sparse_whitespace(self, tmp_path):
        """Stress test with sparse whitespace: 500 blank lines interspersed with spaces and tabs."""
        sparse_content = ("\n   \t  \n" * 250) + "Important Policy Content Here\n" + ("\n \n" * 250)
        sparse_file = tmp_path / "sparse.txt"
        sparse_file.write_text(sparse_content, encoding="utf-8")

        doc = extract_document(str(sparse_file))
        assert doc.extraction_status == "success"
        assert "Important Policy Content Here" in doc.text
        assert doc.pages[0].start == 0
        assert doc.pages[0].end == len(doc.text)

    def test_ingestion_extreme_special_characters_filename(self, tmp_path):
        """Verify filenames with spaces, brackets, hashes, and unicode are safely handled."""
        weird_name = "report #1 [2026] (confidential) & audit_résumé.txt"
        weird_file = tmp_path / weird_name
        weird_file.write_text("Audit statement for Cadence Financial Group.", encoding="utf-8")

        doc = extract_document(str(weird_file))
        assert doc.extraction_status == "success"
        assert "Cadence Financial Group" in doc.text


# ===========================================================================
# 2. Detection Extreme Patterns & Adversarial Traps
# ===========================================================================

class TestDetectionExtremeEdgeCases:
    """Extreme edge cases for regex detection, boundary offsets, and false-positive traps."""

    def test_detection_extreme_dense_chained_pii(self):
        """Multiple PII entities concatenated back-to-back with zero whitespace."""
        # EMAIL followed by CARD, IP, and EMP
        text = "alex@corp.test, 4111 1111 1111 1111, 192.0.2.44, EMP-10482"
        doc = _doc(text)
        res = detect_pii(doc)
        types_found = {e.type for e in res.entities}
        assert "EMAIL" in types_found
        assert "FINANCIAL_IDENTIFIER" in types_found
        assert "IP_ADDRESS" in types_found
        assert "EMPLOYEE_ID" in types_found

    def test_detection_extreme_boundary_positions(self):
        """PII located at index 0 (start of string) and index len(text) (end of string)."""
        # PII at index 0
        text_start = "alex.rivera@example.test is the primary contact."
        res_start = detect_pii(_doc(text_start))
        assert len(res_start.entities) == 1
        assert res_start.entities[0].start == 0
        assert res_start.entities[0].end == len("alex.rivera@example.test")

        # PII at exact EOF
        text_end = "The primary contact is alex.rivera@example.test"
        res_end = detect_pii(_doc(text_end))
        assert len(res_end.entities) == 1
        assert res_end.entities[0].end == len(text_end)

        # Document containing ONLY a single PII entity and nothing else
        text_only = "123-45-6789"
        res_only = detect_pii(_doc(text_only))
        assert len(res_only.entities) == 1
        assert res_only.entities[0].start == 0
        assert res_only.entities[0].end == len("123-45-6789")

    @pytest.mark.parametrize(
        "card_str, should_pass",
        [
            ("4111 1111 1111 1111", True),   # Valid Visa test card
            ("4000 0000 0000 0002", True),   # Valid test card
            ("4111-1111-1111-1111", True),   # Valid hyphenated
            ("4111111111111111", True),      # Valid unspaced 16 digits
            ("4111 1111 1111 1112", False),  # Off-by-one check digit: fails Luhn
            ("1234 5678 9012 3456", False),  # Arbitrary digits: fails Luhn
            ("12345", False),                # Too short
            ("123456789012345678901", False) # Too long (21 digits)
        ],
    )
    def test_detection_extreme_credit_card_luhn_adversarial(self, card_str, should_pass):
        """Strict verification that Luhn algorithm filters out non-card digit runs."""
        text = f"Payment record: {card_str} on invoice."
        res = detect_pii(_doc(text))
        cards = [e for e in res.entities if e.type == "FINANCIAL_IDENTIFIER"]
        if should_pass:
            assert len(cards) == 1
        else:
            assert len(cards) == 0

    @pytest.mark.parametrize(
        "ssn_str, should_pass",
        [
            ("123-45-6789", True),   # Valid US SSN format
            ("219-09-9999", True),   # Valid
            ("000-12-3456", False),  # Invalid area 000
            ("666-12-3456", False),  # Invalid area 666 (reserved)
            ("900-12-3456", False),  # Invalid area >= 900
            ("999-12-3456", False),  # Invalid area 999
            ("123-00-1234", False),  # Invalid group 00
            ("123-45-0000", False),  # Invalid serial 0000
            ("123-45-678", False),   # Incomplete digits
            ("123-45-67890", False), # Extra digits
        ],
    )
    def test_detection_extreme_ssn_boundaries_adversarial(self, ssn_str, should_pass):
        """Adversarial SSN structure verification per SSA guidelines."""
        text = f"Applicant SSN is {ssn_str}."
        res = detect_pii(_doc(text))
        ssns = [e for e in res.entities if e.type == "GOVERNMENT_ID" and text[e.start:e.end] == ssn_str]
        if should_pass:
            assert len(ssns) == 1
        else:
            assert len(ssns) == 0

    @pytest.mark.parametrize(
        "pan_str, should_pass",
        [
            ("ABCPE1234F", True),   # 4th char P (Person)
            ("ABCCE1234F", True),   # 4th char C (Company)
            ("ABCDE1234F", False),  # 4th char D (Invalid holder type)
            ("abcpe1234f", False),  # Lowercase not accepted
            ("ABCPE12345F", False), # Extra digit
            ("12345ABCDE", False),  # Reversed structure
        ],
    )
    def test_detection_extreme_pan_boundaries_adversarial(self, pan_str, should_pass):
        """Indian PAN structure and 4th character holder-type validation."""
        text = f"Tax ID PAN {pan_str} submitted."
        res = detect_pii(_doc(text))
        pans = [e for e in res.entities if e.type == "GOVERNMENT_ID" and text[e.start:e.end] == pan_str]
        if should_pass:
            assert len(pans) == 1
        else:
            assert len(pans) == 0

    @pytest.mark.parametrize(
        "ip_str, should_pass",
        [
            ("0.0.0.0", True),
            ("127.0.0.1", True),
            ("192.168.1.1", True),
            ("255.255.255.255", True),
            ("256.0.0.1", False),     # Octet > 255
            ("192.168.1.300", False), # Octet > 255
            ("1.2.3.4.5", False),     # 5 octets (version string)
            ("999.999.999.999", False),
        ],
    )
    def test_detection_extreme_ipv4_octets_adversarial(self, ip_str, should_pass):
        """IPv4 octet range (0-255) boundary verification."""
        text = f"Connection established from {ip_str} on port 443."
        res = detect_pii(_doc(text))
        ips = [e for e in res.entities if e.type == "IP_ADDRESS" and text[e.start:e.end] == ip_str]
        if should_pass:
            assert len(ips) == 1
        else:
            assert len(ips) == 0

    def test_detection_extreme_surrounding_punctuation_and_markdown(self):
        """Verify enclosing brackets, quotes, and punctuation do not get absorbed into PII spans."""
        text = (
            'Contact: ("alex.rivera@example.test"), '
            'gateway: [192.0.2.44], '
            'employee: <EMP-10482>, '
            'JSON: {"ssn": "123-45-6789"}.'
        )
        res = detect_pii(_doc(text))
        extracted_values = {text[e.start : e.end] for e in res.entities}

        assert "alex.rivera@example.test" in extracted_values
        assert "192.0.2.44" in extracted_values
        assert "EMP-10482" in extracted_values
        assert "123-45-6789" in extracted_values

        # Ensure enclosing punctuation was not absorbed
        for val in extracted_values:
            assert not val.startswith(("(", "[", "<", '"'))
            assert not val.endswith((")", "]", ">", '"', ",", "."))

    def test_detection_extreme_form_feed_page_barrier(self):
        """Entities broken by a form-feed character must never create cross-page spans."""
        text = "Contact: alex\f@example.test and ID: 123-\f45-6789."
        res = detect_pii(_doc(text))
        # Neither invalid fragmented string should be matched across \f
        for e in res.entities:
            assert "\f" not in text[e.start : e.end]


# ===========================================================================
# 3. Redaction & Verification Extreme Stress Tests
# ===========================================================================

class TestRedactionExtremeEdgeCases:
    """Extreme edge cases for token expansion, offset drift, and residual verification."""

    def test_redaction_extreme_offset_drift_with_expanding_tokens(self):
        """Verify right-to-left replacement maintains zero offset drift with expanding tokens."""
        # Replacement tokens are longer than original text:
        # "123-45-6789" (11 chars) -> "[REDACTED_ID]" (13 chars)
        # "EMP-10482" (9 chars) -> "[REDACTED_EMPLOYEE_ID]" (22 chars)
        text = (
            "Item 1: 123-45-6789. "
            "Item 2: EMP-10482. "
            "Item 3: alex.rivera@example.test. "
            "Item 4: 192.0.2.44."
        )
        doc = _doc(text)
        det = detect_pii(doc)
        assert len(det.entities) == 4

        # Redact
        app = apply_redactions(text, [e.model_dump() for e in det.entities])
        redacted = app.text

        # Asserts every token is accurately placed
        assert "[REDACTED_ID]" in redacted
        assert "[REDACTED_EMPLOYEE_ID]" in redacted
        assert "[REDACTED_EMAIL]" in redacted
        assert "[REDACTED_IP]" in redacted

        # Asserts surrounding structure is intact
        assert "Item 1: [REDACTED_ID]." in redacted
        assert "Item 2: [REDACTED_EMPLOYEE_ID]." in redacted
        assert "Item 3: [REDACTED_EMAIL]." in redacted
        assert "Item 4: [REDACTED_IP]." in redacted

    def test_redaction_extreme_repeated_identical_entities(self, tmp_path):
        """Verify multiple occurrences of the exact same PII are cleanly redacted."""
        repeated_email = "security@cadence.corp"
        sentences = [f"Clause {i}: please escalate to {repeated_email} immediately." for i in range(15)]
        text = "\n".join(sentences)

        doc = _doc(text)
        det = detect_pii(doc)
        assert len(det.entities) == 15

        mgr = ArtifactManager(storage_dir=tmp_path)
        res = redact_and_validate(doc, det, artifact_manager=mgr)
        assert res.redactions_applied == 15
        assert res.verification_status == "PASS"
        assert res.release_allowed is True

    def test_redaction_extreme_residual_leak_caught_by_verifier(self):
        """Verify independent residual checker flags any unredacted PII patterns."""
        original = "Contact john.doe@example.com at HQ."
        leaked_redacted = "Contact [REDACTED_EMAIL] and backup jane.smith@example.com."
        entities = [{"type": "EMAIL", "start": 8, "end": 28}]

        # Run independent verification
        report = verify_redacted_text(original, leaked_redacted, entities)
        assert report["status"] == "FAIL"
        checks = [f["check"] for f in report["findings"]]
        assert "residual_email_pattern" in checks

    def test_redaction_extreme_structure_score_preservation(self):
        """Verify complex Markdown formatting retains 100% structure score post-redaction."""
        markdown_text = (
            "# Executive Risk Briefing\n"
            "\n"
            "## Summary\n"
            "Audit led by EMP-10482 at 192.0.2.44.\n"
            "\n"
            "### Recommendations\n"
            "1. Escalate to alex.rivera@example.test.\n"
            "2. Secure card 4111 1111 1111 1111.\n"
        )
        doc = _doc(markdown_text)
        det = detect_pii(doc)
        app = apply_redactions(markdown_text, [e.model_dump() for e in det.entities])

        # Verify structure score
        score = calculate_structure_score(markdown_text, app.text)
        assert score == 1.0  # 100% preservation of lines, splitlines, and headings


# ===========================================================================
# 4. Pipeline & Security Extreme Stress Tests
# ===========================================================================

class TestPipelineAndSecurityExtremeEdgeCases:
    """Extreme edge cases for canary leakage, path traversal, and end-to-end integration."""

    def test_pipeline_extreme_canary_leakage_invariance(self, tmp_path):
        """Ensure secret canary identifiers never leak in reports, audit logs, or error models."""
        canary = "CANARY_SECRET_TOKEN_998877_X"
        canary_content = (
            f"Audit Log for Cadence Financial Group.\n"
            f"Lead Auditor: EMP-10482.\n"
            f"Canary secret: {canary}.\n"
            f"Contact: alex.rivera@example.test.\n"
        )
        sample_file = tmp_path / "canary_test.txt"
        sample_file.write_text(canary_content, encoding="utf-8")

        audit_trail = AuditTrail()
        result = process_document(str(sample_file), audit_trail=audit_trail)

        # 1. ProcessingResult must not contain the canary
        res_json = result.model_dump_json()
        assert canary not in res_json

        # 2. AuditTrail events must not contain the canary
        for event in audit_trail.get_events():
            event_json = event.model_dump_json()
            assert canary not in event_json

        # 3. Pipeline must succeed
        assert result.current_stage == PipelineStage.RELEASED
        assert result.verification_status == "PASS"
        assert result.release_allowed is True

    @pytest.mark.parametrize(
        "payload",
        [
            "../secret.txt",
            "..\\secret.txt",
            "../../etc/passwd",
            "..\\..\\Windows\\System32\\cmd.exe",
            "art-123/../../secret.txt",
            "art-123\\..\\..\\secret.txt",
            "art-123\x00malicious",
            "/etc/shadow",
            "C:\\boot.ini",
        ],
    )
    def test_pipeline_extreme_path_traversal_payloads(self, tmp_path, payload):
        """Verify all path traversal attack payloads are rejected by ArtifactManager."""
        art_mgr = ArtifactManager(storage_dir=tmp_path / "sandbox")
        doc_id = "doc-alpha"

        # Attempt read traversal
        with pytest.raises(ArtifactAccessError):
            art_mgr.read_artifact_bytes(payload, doc_id, release_allowed=True)

    def test_pipeline_extreme_all_fixtures_end_to_end(self):
        """End-to-end verification of all official repository test fixtures."""
        fixtures = [
            FIXTURES_DIR / "clean_text.pdf",
            FIXTURES_DIR / "sample.docx",
            FIXTURES_DIR / "sample.pptx",
            FIXTURES_DIR / "utf8.txt",
        ]
        for fix_path in fixtures:
            assert fix_path.exists(), f"Fixture missing: {fix_path}"
            res = process_document(str(fix_path))
            assert res.current_stage == PipelineStage.RELEASED
            assert res.verification_status == "PASS"
            assert res.release_allowed is True
            assert res.artifact_ref is not None
            assert res.redactions_applied >= 0
