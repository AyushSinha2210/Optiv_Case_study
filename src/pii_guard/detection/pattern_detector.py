"""Deterministic regex rules with format validation.

Confidence values are fixed per rule (see docs/detection.md). They describe
how specific the rule is, not the probability that a span is truly PII.
"""

from __future__ import annotations

import re
from typing import Callable, Optional

from .schemas import Candidate
from .validators import digits_only, ipv4_valid, luhn_valid, pan_valid, ssn_valid, phone_valid

# Each lookaround prevents matching inside a longer token or digit run.
_EMAIL = re.compile(
    r"(?<![\w.+%-])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}(?![\w-])"
)
_SSN = re.compile(r"(?<![\d-])\d{3}-\d{2}-\d{4}(?![\d-])")
_PAN = re.compile(r"(?<![A-Za-z0-9])[A-Z]{5}\d{4}[A-Z](?![A-Za-z0-9])")
# 13 to 19 digits, optionally grouped by single spaces or hyphens.
_CARD = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
_EMPLOYEE = re.compile(r"(?<![A-Za-z0-9])(?:CAD-)?EMP-\d{5}(?!\d)")
_IPV4 = re.compile(
    r"(?<![\d.])(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?!\d)(?!\.\d)"
)
# Accepts international +CC, direct-dial extensions (e.g. +1 (555) 0114), UK/EU/IN/SG/FR formats, multiline table cells, and US numbers.
_PHONE = re.compile(
    r"(?<![\w+])"
    r"(?:"
    r"(?:\+\d{1,3}[\s.-]+)(?:\(\d{1,4}\)[\s.-]*)?(?:\d{1,4}[\s.-]*){2,4}\d{2,4}"
    r"|(?:\+\d{1,3}[\s.-]*)?\(\d{3}\)[\s.-]*\d{3,4}(?:[\s.-]*\d{4})?"
    r"|(?:\+\d{1,3}[\s.-]*)?\(\d{3}\)[\s.-]*\d{4}"
    r"|\b\d{3}[\s.-]\d{3}[\s.-]\d{4}\b"
    r"|\b\d{5}[\s.-]?\d{5}\b"
    r"|\b\d{1,2}[\s.-]+\d{3,4}[\s.-]+\d{4}\b"
    r"|\b\d{1,2}[\s.-]+\d{4}[\s.-]+\d{4}\b"
    r"|\b\d{3}[\s.-]\d{4}\b"
    r")"
    r"(?!\w)"
)

# Deterministic patterns for specific private identifiers & dates (Zero LLM)
_DOB = re.compile(
    r"(?i)\b(?:date[ \t]+of[ \t]+birth|dob|birth[ \t]*date)[ \t]*[:#-][ \t]*"
    r"(?:\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|\d{4}[-/.]\d{1,2}[-/.]\d{1,2}"
    r"|\d{1,2}[ \t]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[,\s]+\d{2,4})\b"
)
_CONSUMER_BILL = re.compile(
    r"(?i)\b(?:consumer|account|bill|invoice|policy)[ \t]+(?:no\.?|num\.?|number|id)[ \t]*[:#-][ \t]*[A-Za-z0-9-]{4,24}\b"
)
_PATIENT_STUDENT_ID = re.compile(
    r"(?i)\b(?:patient|mrn|student|roll|candidate)[ \t]+(?:no\.?|num\.?|number|id)[ \t]*[:#-][ \t]*[A-Za-z0-9-]{4,20}\b"
)
_PROFILE_URL = re.compile(
    r"(?i)\b(?:https?://)?(?:www\.)?"
    r"(?:github\.com/[A-Za-z0-9_%-]{2,39}|leetcode\.com/(?:u/)?[A-Za-z0-9_%-]{2,39}"
    r"|linkedin\.com/in/[A-Za-z0-9_%-]{2,100})\b"
)
_POSTAL_CODE = re.compile(
    r"(?i)\b(?:pin[ \t]*code|pincode|zip[ \t]*code|zipcode|postal[ \t]*code)[ \t]*[:#-][ \t]*\d{5,6}\b"
)

# Stopwords & common section titles that must never be treated as candidate names
_RESUME_HEADER_STOPWORDS = {
    "CURRICULUM VITAE", "RESUME", "CV", "BIO", "BIOGRAPHY",
    "PROFILE", "SUMMARY", "EXECUTIVE SUMMARY", "PROFESSIONAL SUMMARY",
    "EXPERIENCE", "WORK EXPERIENCE", "EMPLOYMENT", "EMPLOYMENT HISTORY",
    "EDUCATION", "ACADEMIC BACKGROUND", "QUALIFICATIONS",
    "SKILLS", "TECHNICAL SKILLS", "CORE COMPETENCIES", "COMPETENCIES",
    "PROJECTS", "PERSONAL PROJECTS", "KEY PROJECTS",
    "CERTIFICATIONS", "LICENSES", "ACHIEVEMENTS", "AWARDS",
    "PUBLICATIONS", "PATENTS", "LANGUAGES", "INTERESTS", "HOBBIES",
    "REFERENCES", "CONTACT", "CONTACT INFO", "CONTACT INFORMATION",
    "DECLARATION", "COVER LETTER", "MEMORANDUM", "REPORT", "AUDIT REPORT",
    "TABLE OF CONTENTS", "CONFIDENTIAL", "CADENCE FINANCIAL GROUP",
    "FINANCIAL REPORT", "TERMS AND CONDITIONS", "POLICY DOCUMENT",
}

_COMMON_WORDS = {
    "THE", "THIS", "THAT", "THESE", "THOSE", "AND", "OR", "BUT", "FOR",
    "WITH", "FROM", "ABOUT", "PAGE", "DATE", "TIME", "STATUS", "NOTE",
    "ORDER", "BATCH", "BUILD", "RELEASE", "VERSION", "TEST", "CHECK",
}

_TITLE_AND_ORG_WORDS = {
    "ENGINEER", "DEVELOPER", "ANALYST", "MANAGER", "ARCHITECT", "DESIGNER",
    "DIRECTOR", "CONSULTANT", "SPECIALIST", "LEAD", "OFFICER", "EXECUTIVE",
    "PRESIDENT", "VICE", "CHAIR", "CHAIRMAN", "CHAIRPERSON", "PROFESSOR",
    "SCIENTIST", "INTERN", "STUDENT", "ASSOCIATE", "PROGRAMMER", "ADMINISTRATOR",
    "COORDINATOR", "SUPERVISOR", "CONTROLLER", "ADVISOR", "AUDITOR", "CHIEF",
    "HEAD", "STAFF", "FOUNDER", "PARTNER", "PRINCIPAL", "TECH", "TECHNICAL",
    "FULL", "STACK", "BACKEND", "FRONTEND", "DEVOPS", "CLOUD", "DATA", "AI",
    "ML", "CYBER", "SECURITY", "FINANCIAL", "ACCOUNT", "LEGAL", "OPERATION",
    "OPERATIONS", "HR", "RECRUITER", "SALES", "MARKETING", "BUSINESS",
    "COMMITTEE", "BOARD", "GROUP", "TEAM", "MEMBER", "CORPORATION", "SERVICES",
    "SYSTEMS", "SOLUTIONS", "TECHNOLOGY", "TECHNOLOGIES", "LABS", "HOLDINGS",
    "VENTURES", "CAPITAL", "BANK", "INVESTMENT", "MANAGEMENT", "UNIVERSITY",
    "COLLEGE", "SCHOOL", "INSTITUTE", "ACADEMY", "DEPARTMENT", "DIVISION",
    "AUTHORIZATION", "AUTHENTICATION", "CONFIDENTIAL", "MEMORANDUM",
}

_NON_PERSON_PREFIXES = {
    "FILE", "DB", "DATABASE", "DOMAIN", "USER", "USERNAME", "PROJECT",
    "SERVER", "HOST", "BUCKET", "TABLE", "SCHEMA", "CLASS", "INTERFACE",
}


def _is_valid_person_name(name_candidate: str) -> bool:
    clean = name_candidate.strip(" ,;:\t\r\n")
    if not clean or len(clean) < 3 or len(clean) > 40:
        return False
    if "\n" in clean or "\r" in clean or "\f" in clean:
        return False
    upper = clean.upper()
    if upper in _RESUME_HEADER_STOPWORDS or upper in _COMMON_WORDS:
        return False
    words = clean.split()
    if not 2 <= len(words) <= 4:
        return False
    for w in words:
        w_clean = w.strip(".,'")
        if not w_clean.isalpha():
            return False
        w_upper = w_clean.upper()
        if w_upper in _COMMON_WORDS or w_upper in _TITLE_AND_ORG_WORDS:
            return False
        if len(w_clean) < 2 and not (len(w) == 2 and w[1] == "."):
            return False
    # Must be Title Case or ALL UPPERCASE
    is_title = all(w[0].isupper() and (w[1:].islower() or w.endswith(".")) for w in words if len(w) > 1)
    is_upper = clean.isupper()
    return is_title or is_upper


def _detect_labeled_and_resume_names(text: str) -> list[Candidate]:
    candidates: list[Candidate] = []
    discovered_names: set[str] = set()

    # 1. Explicitly labeled names: Name: Ayush Sinha, Candidate Name: ..., etc.
    labeled_pattern = re.compile(
        r"(?i)\b(?P<prefix>candidate[ \t]*name|applicant[ \t]*name|full[ \t]*name|student[ \t]*name|"
        r"employee[ \t]*name|client[ \t]*name|customer[ \t]*name|contact[ \t]*person|name)"
        r"[ \t]*[:#-][ \t]*"
        r"(?P<val>[A-Z][a-zA-Z'.-]+(?:[ \t]+[A-Z][a-zA-Z'.-]+){1,3})"
        r"(?=\b|[\r\n,;|])"
    )
    for m in labeled_pattern.finditer(text):
        prefix_start = m.start("prefix")
        preceding = text[max(0, prefix_start - 20) : prefix_start].upper().split()
        if preceding and preceding[-1] in _NON_PERSON_PREFIXES:
            continue
        val = m.group("val").strip()
        start = m.start("val")
        end = start + len(val)
        if _is_valid_person_name(val):
            candidates.append(Candidate(type="PERSON", start=start, end=end, confidence=0.95, source="pattern"))
            discovered_names.add(val)

    # 2. Honorifics: Mr. Ayush Sinha, Dr. Julian Thorne, etc.
    honorific_pattern = re.compile(
        r"\b(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)[ \t]+"
        r"([A-Z][a-zA-Z'.-]+(?:[ \t]+[A-Z][a-zA-Z'.-]+){1,3})"
        r"(?=\b|[\r\n,;|])"
    )
    for m in honorific_pattern.finditer(text):
        val = m.group(1).strip()
        start = m.start(1)
        end = start + len(val)
        if _is_valid_person_name(val):
            candidates.append(Candidate(type="PERSON", start=start, end=end, confidence=0.90, source="pattern"))
            discovered_names.add(val)

    # 3. Resume Header Candidate Name:
    # On a resume, candidate name is in the first 3 non-empty lines,
    # accompanied by an email, phone, or profile URL in the top 1500 chars.
    has_contact_in_header = bool(
        re.search(r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text[:1500]) or
        re.search(r"\+?\d[\d\s().-]{7,}\d", text[:1500]) or
        re.search(r"(?i)linkedin\.com|github\.com", text[:1500])
    )

    if has_contact_in_header:
        lines = text.splitlines(keepends=True)
        offset = 0
        found_header_name = False
        non_empty_count = 0
        for line in lines:
            stripped = line.strip()
            if stripped:
                non_empty_count += 1
                if non_empty_count <= 3 and not found_header_name:
                    if _is_valid_person_name(stripped):
                        line_start = offset + line.find(stripped)
                        line_end = line_start + len(stripped)
                        candidates.append(
                            Candidate(type="PERSON", start=line_start, end=line_end, confidence=0.88, source="pattern")
                        )
                        discovered_names.add(stripped)
                        found_header_name = True
                elif non_empty_count > 3:
                    break
            offset += len(line)

    # 4. Search for recurring mentions of any detected candidate name across document
    for name in discovered_names:
        escaped = re.escape(name)
        pattern = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
        for m in pattern.finditer(text):
            start = m.start()
            end = m.end()
            if not any(c.start == start and c.end == end for c in candidates):
                candidates.append(Candidate(type="PERSON", start=start, end=end, confidence=0.88, source="pattern"))

    return candidates

_Validator = Optional[Callable[[str], bool]]

_RULES: tuple[tuple[str, re.Pattern[str], float, _Validator], ...] = (
    ("EMAIL", _EMAIL, 0.98, None),
    ("GOVERNMENT_ID", _SSN, 0.97, ssn_valid),
    ("GOVERNMENT_ID", _PAN, 0.95, pan_valid),
    ("GOVERNMENT_ID", _DOB, 0.95, None),
    ("FINANCIAL_IDENTIFIER", _CARD, 0.99, lambda s: luhn_valid(digits_only(s))),
    ("FINANCIAL_IDENTIFIER", _CONSUMER_BILL, 0.95, None),
    ("EMPLOYEE_ID", _EMPLOYEE, 0.95, None),
    ("EMPLOYEE_ID", _PATIENT_STUDENT_ID, 0.95, None),
    ("EMPLOYEE_ID", _PROFILE_URL, 0.95, None),
    ("ADDRESS", _POSTAL_CODE, 0.90, None),
    ("IP_ADDRESS", _IPV4, 0.90, ipv4_valid),
    ("PHONE", _PHONE, 0.80, phone_valid),
)


def detect_patterns(text: str) -> list[Candidate]:
    """Return validated pattern candidates with offsets into `text`."""
    candidates: list[Candidate] = []
    for pii_type, regex, confidence, validator in _RULES:
        for match in regex.finditer(text):
            value = match.group(0)
            if "\f" in value:  # page boundary; never a PII span
                continue
            if validator is not None and not validator(value):
                continue
            candidates.append(
                Candidate(
                    type=pii_type,
                    start=match.start(),
                    end=match.end(),
                    confidence=confidence,
                    source="pattern",
                )
            )

    # Extract deterministic and contextual person names (resumes, labels, honorifics)
    name_candidates = _detect_labeled_and_resume_names(text)
    candidates.extend(name_candidates)
    return candidates

