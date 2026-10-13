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
    return candidates
