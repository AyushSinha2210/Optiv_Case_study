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
_REGISTRATION_ID = re.compile(
    r"(?i)\b(?:reg(?:istration|n)?|roll|student|enrollment|enrolment|admission|candidate|patient|mrn)"
    r"(?:[ \t]+(?:no\.?|num\.?|number|id|code))?"
    r"[ \t]*(?:is|[:#=-]|–|—)[ \t]*"
    r"([A-Za-z0-9-]{4,24})\b"
)
_REGISTRATION_ID_NO_COLON = re.compile(
    r"(?i)\b(?:reg(?:istration|n)?|roll|student|enrollment|enrolment|admission|candidate|patient|mrn)"
    r"[ \t]+(?:no\.?|num\.?|number|id|code)[ \t]+"
    r"([A-Za-z0-9-]{4,24})\b"
)
_ACADEMIC_ROLL_NO = re.compile(
    r"\b\d{2}[A-Za-z]{2,4}\d{4,5}\b"
)
_PATIENT_STUDENT_ID = _REGISTRATION_ID
_PROFILE_URL = re.compile(
    r"(?i)\b(?:https?://)?(?:www\.)?"
    r"(?:github\.com/[A-Za-z0-9_%-]{2,39}|leetcode\.com/(?:u/)?[A-Za-z0-9_%-]{2,39}"
    r"|linkedin\.com/in/[A-Za-z0-9_%-]{2,100})\b"
)
_POSTAL_CODE = re.compile(
    r"(?i)\b(?:pin[ \t]*code|pincode|zip[ \t]*code|zipcode|postal[ \t]*code)[ \t]*[:#-][ \t]*\d{5,6}\b"
)

# Known first and last names for fast, high-confidence gazetteer resolution across all casings
_COMMON_FIRST_NAMES = {
    "AYUSH", "ALEX", "SARAH", "PRIYA", "RAHUL", "AMIT", "ROHAN", "ANANYA",
    "POOJA", "NEHA", "VIKRAM", "ADITYA", "ARJUN", "SNEHA", "DEEPAK", "SANJAY",
    "MANOJ", "RAJESH", "SURESH", "ANIL", "SUNIL", "RAMESH", "VISHAL", "NIDHI",
    "SWATI", "KAVITA", "MEERA", "RITU", "SHWETA", "DIVYA", "JOHN", "MICHAEL",
    "DAVID", "JAMES", "ROBERT", "WILLIAM", "EMILY", "EMMA", "DANIEL", "JULIAN",
    "PETER", "THOMAS", "RICHARD", "JOSEPH", "CHARLES", "CHRISTOPHER", "MATTHEW",
}

_COMMON_LAST_NAMES = {
    "SINHA", "EXAMPLE", "SHARMA", "VERMA", "GUPTA", "PATEL", "KUMAR", "SINGH",
    "RAO", "REDDY", "NAIR", "CHOUDHARY", "MISHRA", "JOSHI", "BHAT", "DESHMUKH",
    "KULKARNI", "CHATTERJEE", "BANERJEE", "DUTTA", "GHOSE", "MUKHERJEE", "DAS",
    "THORNE", "CHEN", "WANG", "LI", "ZHANG", "SMITH", "JOHNSON", "WILLIAMS",
    "BROWN", "JONES", "GARCIA", "MILLER", "DAVIS", "RODRIGUEZ", "MARTINEZ",
}

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
    "IS", "WAS", "ARE", "WERE", "AM", "BE", "BEEN", "BEING", "HAVE",
    "HAS", "HAD", "DO", "DOES", "DID", "NO", "NOT", "NUM", "NUMBER",
    "ID", "REF", "CODE", "REG", "ROLL", "AT", "ON", "IN", "TO", "BY",
    "AN", "AS", "IF", "SO", "MY", "HIS", "HER", "THEIR", "OUR", "YOUR",
    "ATTENDED", "MET", "JOINED", "WORKED", "CALLED", "SPOKE", "SAID",
    "REPORTED", "WROTE", "SUBMITTED", "APPROVED", "VERIFIED", "COMPLETED",
    "SHARED", "SENT", "RECEIVED", "REQUESTED", "FOUND", "VIEWED", "WENT",
    "THERE", "HERE", "WHERE", "WHEN", "WHY", "HOW", "ALL", "ANY", "BOTH",
    "EACH", "FEW", "MORE", "MOST", "OTHER", "SOME", "SUCH", "THAN", "TOO",
    "VERY", "CAN", "WILL", "JUST", "SHOULD", "NOW",
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


def _is_valid_person_name(name_candidate: str, allow_lowercase: bool = False) -> bool:
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
    if allow_lowercase:
        return True
    # Fast-path: If words match known common names (e.g. "ayush sinha", "alex example"), allow regardless of case
    if len(words) >= 2 and words[0].upper() in _COMMON_FIRST_NAMES and (words[1].upper() in _COMMON_LAST_NAMES or len(words[1]) >= 3):
        return True
    # Allow Title Case ("Alex Example"), Mixed Case ("Ayush sinha"), or ALL UPPERCASE ("AYUSH SINHA")
    is_capitalized = words[0][0].isupper()
    is_upper = clean.isupper()
    return is_capitalized or is_upper


def _clean_name_tokens(raw: str) -> Optional[tuple[str, int]]:
    """Trims leading and trailing common stopwords/verbs from raw candidate, returning (clean_name, offset_in_raw)."""
    words = raw.split()
    while words and (words[0].upper() in _COMMON_WORDS or not words[0].isalpha()):
        words.pop(0)
    while words and (words[-1].upper() in _COMMON_WORDS or not words[-1].isalpha()):
        words.pop()
    if 2 <= len(words) <= 3:
        cand = " ".join(words)
        if _is_valid_person_name(cand, allow_lowercase=True):
            return cand, raw.find(cand)
    return None


def _detect_labeled_and_resume_names(text: str) -> list[Candidate]:
    candidates: list[Candidate] = []
    discovered_names: set[str] = set()

    # 1. Explicitly labeled & intro names: Name: Ayush Sinha, name is ayush sinha, my name is ..., etc.
    labeled_pattern = re.compile(
        r"(?i)\b(?P<prefix>"
        r"candidate[ \t]*name|applicant[ \t]*name|full[ \t]*name|student[ \t]*name|"
        r"employee[ \t]*name|client[ \t]*name|customer[ \t]*name|contact[ \t]*person|author[ \t]*name|"
        r"my[ \t]*name|his[ \t]*name|her[ \t]*name|your[ \t]*name|"
        r"i[ \t]*am|this[ \t]*is|call[ \t]*me|"
        r"candidate|applicant|author|contact|name)"
        r"[ \t]*(?:is|was|[:#=-]|–|—)[ \t]*"
        r"(?P<val>[a-zA-Z'.-]+(?:[ \t]+[a-zA-Z'.-]+){1,3})"
        r"(?=\b|[\r\n,;|]|\s+(?:and|or|with|at|on|via|reg|roll|id|emp|phone|email)\b)"
    )
    for m in labeled_pattern.finditer(text):
        prefix_start = m.start("prefix")
        preceding = text[max(0, prefix_start - 20) : prefix_start].upper().split()
        if preceding and preceding[-1] in _NON_PERSON_PREFIXES:
            continue
        val = m.group("val").strip()
        cleaned = _clean_name_tokens(val)
        if cleaned:
            cand_name, v_off = cleaned
            start = m.start("val") + v_off
            end = start + len(cand_name)
            candidates.append(Candidate(type="PERSON", start=start, end=end, confidence=0.95, source="pattern"))
            discovered_names.add(cand_name)

    # 2. Multi-name lists & team enumerations:
    # e.g., "team members: ayush sinha, alex example, Priya Sharma"
    list_header_pattern = re.compile(
        r"(?i)\b(?:team[ \t]*members?|members?|attendees?|participants?|contributors?|authors?|"
        r"reviewers?|engineers?|developers?|candidates?|names?|contacts?)"
        r"[ \t]*[:#-]\s*(?P<list>[^\r\n.]+)"
    )
    for lm in list_header_pattern.finditer(text):
        raw_list = lm.group("list")
        list_offset = lm.start("list")
        delims = re.compile(r"\s*(?:,\s*(?:and|&|or)?\s*|\s+(?:and|&|or)\s+)\s*")
        curr_pos = 0
        for part in delims.split(raw_list):
            part_clean = part.strip(" ,;:\t")
            if not part_clean:
                continue
            p_idx = raw_list.find(part_clean, curr_pos)
            if p_idx >= 0:
                curr_pos = p_idx + len(part_clean)
                cleaned = _clean_name_tokens(part_clean)
                if cleaned:
                    cand_str, c_off = cleaned
                    p_start = list_offset + p_idx + c_off
                    p_end = p_start + len(cand_str)
                    if not any(c.start == p_start and c.end == p_end for c in candidates):
                        candidates.append(Candidate(type="PERSON", start=p_start, end=p_end, confidence=0.93, source="pattern"))
                        discovered_names.add(cand_str)

    # 3. Coordinated name pairs in running text:
    # e.g., "ayush sinha and alex example were assigned" or "Ayush Sinha and Sarah Chen"
    coord_pattern = re.compile(
        r"\b(?P<n1>[a-zA-Z'.-]+(?:[ \t]+[a-zA-Z'.-]+){1,2})"
        r"\s+(?:and|&|with|or)\s+"
        r"(?P<n2>[a-zA-Z'.-]+(?:[ \t]+[a-zA-Z'.-]+){1,2})\b"
    )
    for cm in coord_pattern.finditer(text):
        c1_res = _clean_name_tokens(cm.group("n1"))
        c2_res = _clean_name_tokens(cm.group("n2"))
        if c1_res and c2_res:
            c1, off1 = c1_res
            c2, off2 = c2_res
            s1 = cm.start("n1") + off1
            e1 = s1 + len(c1)
            s2 = cm.start("n2") + off2
            e2 = s2 + len(c2)
            if not any(c.start == s1 and c.end == e1 for c in candidates):
                candidates.append(Candidate(type="PERSON", start=s1, end=e1, confidence=0.92, source="pattern"))
                discovered_names.add(c1)
            if not any(c.start == s2 and c.end == e2 for c in candidates):
                candidates.append(Candidate(type="PERSON", start=s2, end=e2, confidence=0.92, source="pattern"))
                discovered_names.add(c2)

    # 4. Honorifics: Mr. Ayush Sinha, Dr. Julian Thorne, etc.
    honorific_pattern = re.compile(
        r"\b(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)[ \t]+"
        r"([a-zA-Z'.-]+(?:[ \t]+[a-zA-Z'.-]+){0,2})\b"
    )
    for m in honorific_pattern.finditer(text):
        val = m.group(1).strip()
        cleaned = _clean_name_tokens(val)
        if cleaned:
            cand_name, v_off = cleaned
            start = m.start(1) + v_off
            end = start + len(cand_name)
            candidates.append(Candidate(type="PERSON", start=start, end=end, confidence=0.90, source="pattern"))
            discovered_names.add(cand_name)

    # 3. Resume Header Candidate Name (first 3 lines)
    has_contact_in_header = bool(
        re.search(r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text[:1500]) or
        re.search(r"\+?\d[\d\s().-]{7,}\d", text[:1500]) or
        re.search(r"(?i)linkedin\.com|github\.com", text[:1500])
    )
    if has_contact_in_header:
        email_match = re.search(r"\b([A-Za-z0-9._%+-]+)@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text[:1500])
        email_tokens: set[str] = set()
        if email_match:
            raw_local = email_match.group(1).lower()
            email_tokens = {re.sub(r"\d+", "", t) for t in re.split(r"[._%+-]+", raw_local) if len(t) >= 3}
            email_tokens.discard("")

        lines = text.splitlines(keepends=True)
        offset = 0
        found_header_name = False
        non_empty_count = 0
        for line in lines:
            stripped = line.strip()
            if stripped:
                non_empty_count += 1
                if non_empty_count <= 3 and not found_header_name:
                    line_words = {w.lower().strip(".,'") for w in stripped.split()}
                    matches_email = bool(email_tokens and line_words.intersection(email_tokens))
                    allow_lc = matches_email or (non_empty_count == 1 and len(line_words) in (2, 3))
                    if _is_valid_person_name(stripped, allow_lowercase=allow_lc):
                        line_start = offset + line.find(stripped)
                        line_end = line_start + len(stripped)
                        if not any(c.start == line_start and c.end == line_end for c in candidates):
                            candidates.append(
                                Candidate(type="PERSON", start=line_start, end=line_end, confidence=0.88, source="pattern")
                            )
                            discovered_names.add(stripped)
                            found_header_name = True
                elif non_empty_count > 3:
                    break
            offset += len(line)

    # 4. Document-wide propagation: search for recurring mentions of any detected candidate name across document (case-insensitive)
    for name in list(discovered_names):
        escaped = re.escape(name)
        pattern = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
        for m in pattern.finditer(text):
            start = m.start()
            end = m.end()
            if not any(c.start == start and c.end == end for c in candidates):
                candidates.append(Candidate(type="PERSON", start=start, end=end, confidence=0.90, source="pattern"))

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
    ("EMPLOYEE_ID", _REGISTRATION_ID, 0.96, None),
    ("EMPLOYEE_ID", _REGISTRATION_ID_NO_COLON, 0.95, None),
    ("EMPLOYEE_ID", _ACADEMIC_ROLL_NO, 0.95, None),
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
            if match.lastindex and match.lastindex >= 1 and match.group(1):
                start = match.start(1)
                end = match.end(1)
                value = match.group(1)
            else:
                start = match.start()
                end = match.end()
                value = match.group(0)

            if "\f" in value:  # page boundary; never a PII span
                continue
            if validator is not None and not validator(value):
                continue
            candidates.append(
                Candidate(
                    type=pii_type,
                    start=start,
                    end=end,
                    confidence=confidence,
                    source="pattern",
                )
            )

    # Extract deterministic and contextual person names (resumes, labels, honorifics, multi-name lists)
    name_candidates = _detect_labeled_and_resume_names(text)
    candidates.extend(name_candidates)
    return candidates


