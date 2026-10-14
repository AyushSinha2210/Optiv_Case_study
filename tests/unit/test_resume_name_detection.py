"""Tests for Candidate and Person Name detection on Resumes, CVs, and Profiles."""

from types import SimpleNamespace
import pytest

from src.pii_guard.detection.detector import detect_pii, PIIDetector
from src.pii_guard.detection.ner_detector import get_default_ner_backend
from src.pii_guard.redaction.redactor import apply_redactions
from src.pii_guard.redaction.policy import get_replacement
from src.pii_guard.redaction.verifier import verify_redacted_text


def _doc(text: str, doc_id: str = "doc-resume-test") -> SimpleNamespace:
    return SimpleNamespace(document_id=doc_id, text=text, extraction_status="success")


class TestResumeCandidateNameDetection:
    """Validate that candidate and author names are detected, flagged, and redacted on resumes."""

    def test_resume_header_all_caps_name_detection(self):
        """Header candidate name in ALL CAPS (e.g. AYUSH SINHA) followed by contact block."""
        text = (
            "AYUSH SINHA\n"
            "Software & AI Security Engineer\n"
            "Email: ayush22.sinha@gmail.com\n"
            "Phone: +91 98765 43210\n"
            "Bangalore, India | linkedin.com/in/ayush-sinha\n\n"
            "EXPERIENCE\n"
            "Software Engineer - Privacy Core\n"
            "- Ayush Sinha designed and validated fail-closed release gates."
        )
        res = detect_pii(_doc(text))
        persons = [text[e.start : e.end] for e in res.entities if e.type == "PERSON"]

        assert "AYUSH SINHA" in persons
        assert "Ayush Sinha" in persons

        # Redaction check
        red = apply_redactions(text, [e.model_dump() for e in res.entities])
        assert "AYUSH SINHA" not in red.text
        assert "Ayush Sinha" not in red.text
        assert "[REDACTED_PERSON]" in red.text
        assert "[REDACTED_EMAIL]" in red.text

        # Independent verification check
        ver = verify_redacted_text(text, red.text, [e.model_dump() for e in res.entities])
        assert ver["status"] == "PASS"
        assert ver["findings"] == []

    def test_resume_header_title_case_name_detection(self):
        """Header candidate name in Title Case (e.g. Ayush Sinha)."""
        text = (
            "Ayush Sinha\n"
            "Full Stack Developer\n"
            "ayush22.sinha@gmail.com | +91-9876543210\n\n"
            "SUMMARY\n"
            "Passionate engineer with deep expertise in Python, PyMuPDF, and OCR."
        )
        res = detect_pii(_doc(text))
        persons = [text[e.start : e.end] for e in res.entities if e.type == "PERSON"]
        assert "Ayush Sinha" in persons

    def test_explicitly_labeled_names(self):
        """Explicit labels like Name:, Candidate Name:, Applicant Name:, Author:."""
        text = (
            "Candidate Name: Ayush Sinha\n"
            "Applicant Name: Johnathan Doe\n"
            "Contact Person: Jane Smith\n"
            "Account: CAD-EMP-10482"
        )
        res = detect_pii(_doc(text))
        persons = {text[e.start : e.end] for e in res.entities if e.type == "PERSON"}
        assert "Ayush Sinha" in persons
        assert "Johnathan Doe" in persons
        assert "Jane Smith" in persons

    def test_honorific_salutation_name_detection(self):
        """Honorific titles (Mr., Ms., Dr., Prof.)."""
        text = "Audit lead Dr. Julian Thorne approved report for Mr. Ayush Sinha."
        res = detect_pii(_doc(text), ner_backend=get_default_ner_backend())
        persons = {text[e.start : e.end] for e in res.entities if e.type == "PERSON"}
        assert "Julian Thorne" in persons or "Dr. Julian Thorne" in persons
        assert "Ayush Sinha" in persons

    def test_resume_section_headers_are_not_flagged(self):
        """Standard resume headers and job titles must never be falsely flagged as names."""
        text = (
            "RESUME\n"
            "PROFESSIONAL SUMMARY\n"
            "WORK EXPERIENCE\n"
            "TECHNICAL SKILLS\n"
            "EDUCATION\n"
            "CORE COMPETENCIES\n"
            "CERTIFICATIONS\n"
            "CADENCE FINANCIAL GROUP"
        )
        res = detect_pii(_doc(text))
        persons = [e for e in res.entities if e.type == "PERSON"]
        assert persons == []

    def test_technical_metadata_names_are_not_flagged(self):
        """Technical metadata keys (file name, db name, username) must not be flagged."""
        text = (
            "File name: report_export.pdf\n"
            "Database name: cadence_dw_prod\n"
            "User name: admin_svc_acct"
        )
        res = detect_pii(_doc(text))
        persons = [e for e in res.entities if e.type == "PERSON"]
        assert persons == []

    def test_policy_replacement_for_name_aliases(self):
        """DEFAULT_POLICY maps NAME and PERSON_NAME cleanly to [REDACTED_PERSON]."""
        assert get_replacement("PERSON") == "[REDACTED_PERSON]"
        assert get_replacement("NAME") == "[REDACTED_PERSON]"
        assert get_replacement("PERSON_NAME") == "[REDACTED_PERSON]"
        assert get_replacement("CANDIDATE_NAME") == "[REDACTED_PERSON]"
