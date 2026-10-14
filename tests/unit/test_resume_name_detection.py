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

    def test_lowercase_and_mixed_case_name_detection(self):
        """Verify 'ayush sinha', 'Ayush sinha', and 'Alex Example' are accurately detected."""
        # 1. Labeled lowercase: 'Name: ayush sinha'
        res1 = detect_pii(_doc("Name: ayush sinha\nEmail: ayush@example.com"))
        assert any(e.type == "PERSON" and "ayush sinha" in "Name: ayush sinha\nEmail: ayush@example.com"[e.start:e.end] for e in res1.entities)

        # 2. Labeled mixed-case: 'Name: Ayush sinha'
        res2 = detect_pii(_doc("Name: Ayush sinha\nEmail: ayush@example.com"))
        assert any(e.type == "PERSON" and "Ayush sinha" in "Name: Ayush sinha\nEmail: ayush@example.com"[e.start:e.end] for e in res2.entities)

        # 3. Resume header lowercase with email: 'ayush sinha'
        res3 = detect_pii(_doc("ayush sinha\nSoftware Engineer\nayush22.sinha@gmail.com\n+91 9876543210"))
        assert any(e.type == "PERSON" and "ayush sinha" in "ayush sinha\nSoftware Engineer\nayush22.sinha@gmail.com\n+91 9876543210"[e.start:e.end] for e in res3.entities)

        # 4. Resume header mixed case: 'Ayush sinha'
        res4 = detect_pii(_doc("Ayush sinha\nSoftware Engineer\nayush22.sinha@gmail.com\n+91 9876543210"))
        assert any(e.type == "PERSON" and "Ayush sinha" in "Ayush sinha\nSoftware Engineer\nayush22.sinha@gmail.com\n+91 9876543210"[e.start:e.end] for e in res4.entities)

        # 5. Title case: 'Alex Example'
        res5 = detect_pii(_doc("Alex Example\nSoftware Engineer\nalex@example.com\n+1 (555) 0199"))
        assert any(e.type == "PERSON" and "Alex Example" in "Alex Example\nSoftware Engineer\nalex@example.com\n+1 (555) 0199"[e.start:e.end] for e in res5.entities)

    def test_alex_example_name_detection_variations(self):
        """Validate Alex Example across Title Case, all-lowercase, mixed-case, and recurring mentions."""
        # A. Title Case in header and recurring body mention
        text1 = (
            "Alex Example\n"
            "Cloud Security Architect\n"
            "Email: alex.example@company.com\n"
            "Phone: (555) 123-4567\n\n"
            "SUMMARY\n"
            "Alex Example is a certified lead architect who engineered PII safeguards."
        )
        res1 = detect_pii(_doc(text1))
        matched1 = [text1[e.start:e.end] for e in res1.entities if e.type == "PERSON"]
        assert "Alex Example" in matched1
        assert matched1.count("Alex Example") == 2

        # B. All-lowercase: 'alex example'
        text2 = (
            "alex example\n"
            "Software Engineer\n"
            "alex.example@gmail.com\n"
            "+1-555-987-6543\n\n"
            "Projects by alex example in privacy governance."
        )
        res2 = detect_pii(_doc(text2))
        matched2 = [text2[e.start:e.end].lower() for e in res2.entities if e.type == "PERSON"]
        assert "alex example" in matched2

        # C. Mixed case: 'Alex example'
        text3 = (
            "Alex example\n"
            "Data Analyst\n"
            "alex@example.org\n"
            "+1 (555) 321-7654"
        )
        res3 = detect_pii(_doc(text3))
        matched3 = [text3[e.start:e.end] for e in res3.entities if e.type == "PERSON"]
        assert "Alex example" in matched3

        # D. Labeled: 'Candidate: Alex Example' and 'Applicant: alex example'
        text4 = (
            "Candidate: Alex Example\n"
            "Applicant: alex example\n"
            "Contact Person: Alex Example"
        )
        res4 = detect_pii(_doc(text4))
        matched4 = [text4[e.start:e.end] for e in res4.entities if e.type == "PERSON"]
        assert "Alex Example" in matched4
        assert "alex example" in matched4

        # E. Redaction and Verification of Alex Example
        red = apply_redactions(text1, [e.model_dump() for e in res1.entities])
        assert "Alex Example" not in red.text
        assert "[REDACTED_PERSON]" in red.text
        ver = verify_redacted_text(text1, red.text, [e.model_dump() for e in res1.entities])
        assert ver["status"] == "PASS"
        assert ver["findings"] == []

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

    def test_user_phrase_name_and_reg_no_detection(self):
        """Verify exact user phrase: 'name is ayush sinha and Reg. no. is 24BCI0119'."""
        text = "name is ayush sinha and Reg. no. is 24BCI0119"
        res = detect_pii(_doc(text))

        persons = [text[e.start:e.end] for e in res.entities if e.type == "PERSON"]
        employee_ids = [text[e.start:e.end] for e in res.entities if e.type == "EMPLOYEE_ID"]

        assert "ayush sinha" in persons
        assert "24BCI0119" in employee_ids

        # Redaction verification
        red = apply_redactions(text, [e.model_dump() for e in res.entities])
        assert "ayush sinha" not in red.text
        assert "24BCI0119" not in red.text
        assert "[REDACTED_PERSON]" in red.text
        assert "[REDACTED_EMPLOYEE_ID]" in red.text
        assert red.text == "name is [REDACTED_PERSON] and Reg. no. is [REDACTED_EMPLOYEE_ID]"

    def test_multi_name_sentence_all_names_detected(self):
        """Verify multiple names in one sentence: neither is omitted."""
        # 1. Coordinated pair in lowercase
        text1 = "ayush sinha and alex example were assigned to lead the privacy engineering team"
        res1 = detect_pii(_doc(text1))
        matched1 = [text1[e.start:e.end] for e in res1.entities if e.type == "PERSON"]
        assert "ayush sinha" in matched1
        assert "alex example" in matched1

        # 2. Enumerated team list
        text2 = "team members: ayush sinha, alex example, Priya Sharma"
        res2 = detect_pii(_doc(text2))
        matched2 = [text2[e.start:e.end] for e in res2.entities if e.type == "PERSON"]
        assert "ayush sinha" in matched2
        assert "alex example" in matched2
        assert "Priya Sharma" in matched2

        # 3. Action sentence with multiple names
        text3 = "The review was conducted by Ayush Sinha and Sarah Chen."
        res3 = detect_pii(_doc(text3))
        matched3 = [text3[e.start:e.end] for e in res3.entities if e.type == "PERSON"]
        assert "Ayush Sinha" in matched3
        assert "Sarah Chen" in matched3

    def test_registration_and_academic_roll_numbers(self):
        """Verify registration and roll numbers across formats."""
        cases = [
            ("Reg. no. is 24BCI0119", "24BCI0119"),
            ("Reg. no: 24BCI0119", "24BCI0119"),
            ("Registration Number is 24BCI0119", "24BCI0119"),
            ("Roll no: 24BCI0119", "24BCI0119"),
            ("Student ID: 24BCI0119", "24BCI0119"),
            ("Student 24BCI0119 was present at the session", "24BCI0119"),
            ("Roll No. 21BCE1042 submitted.", "21BCE1042"),
        ]
        for sentence, expected_val in cases:
            res = detect_pii(_doc(sentence))
            emp_ids = [sentence[e.start:e.end] for e in res.entities if e.type == "EMPLOYEE_ID"]
            assert expected_val in emp_ids, f"Expected {expected_val} in {sentence}, found: {emp_ids}"

    def test_image_bearing_document_not_blocked(self, tmp_path, monkeypatch):
        """Documents with images (and benign OCR warnings like WARN_OCR_NO_TEXT) are not blocked."""
        from src.pii_guard.orchestration import pipeline
        from src.pii_guard.ingestion.schemas import ExtractedDocument, PageInfo, WarningInfo

        source = tmp_path / "resume_with_photo.txt"
        source.write_text("Ayush Sinha\nReg. no. is 24BCI0119\nSoftware Engineer", encoding="utf-8")

        # Mock extractor returning success with informational image warning
        doc_obj = ExtractedDocument(
            document_id="doc-img-test",
            source_type="pdf",
            text="Ayush Sinha\nReg. no. is 24BCI0119\nSoftware Engineer",
            pages=[
                PageInfo(
                    index=1,
                    label="page",
                    start=0,
                    end=48,
                    method="mixed",
                    ocr_confidence=75.0,
                    char_count=48,
                    warnings=["WARN_OCR_NO_TEXT"],
                )
            ],
            warnings=[WarningInfo(code="WARN_OCR_NO_TEXT", message="Image had no text", page=1)],
            extraction_status="success",
        )

        monkeypatch.setattr(pipeline, "extract_document", lambda *_args, **_kwargs: doc_obj)
        res = pipeline.process_document(str(source))

        assert res.workflow_status == "success"
        assert res.release_allowed is True
        assert res.current_stage.value == "RELEASED"
        assert res.artifact_ref is not None



