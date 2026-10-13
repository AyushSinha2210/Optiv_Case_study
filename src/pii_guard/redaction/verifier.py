"""Independent checks for redacted text and saved artifacts."""

from __future__ import annotations

import ipaddress
import re
from collections.abc import Callable, Iterable, Mapping
from typing import Any

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")
GOVERNMENT_ID_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CARD_PATTERN = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
IP_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def _luhn_valid(value: str) -> bool:
    digits = [int(char) for char in value if char.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


def _is_residual_phone(value: str) -> bool:
    clean = value.strip()
    if re.fullmatch(r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2}", clean):
        return False
    if re.fullmatch(r"\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}", clean):
        return False
    # Clause and exception codes like EXC-2026-041 13.1 or ISS-2025-0431
    if re.search(r"\b202[0-9]-\d{3,4}\b", clean) or re.search(r"\.\d\b", clean):
        return False
    digits = [c for c in clean if c.isdigit()]
    if len(digits) == 8 and clean.count("-") == 2:
        return False
    return len(digits) in (10, 11) or (clean.startswith("+") and 8 <= len(digits) <= 15)


def _is_residual_ssn(value: str) -> bool:
    parts = value.split("-")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        return False
    area, group, serial = parts
    area_n = int(area)
    if area_n == 0 or area_n == 666 or area_n >= 900:
        return False
    return int(group) != 0 and int(serial) != 0


def _residual_findings(text: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if EMAIL_PATTERN.search(text):
        findings.append({"check": "residual_email_pattern", "entity_type": "EMAIL"})
    if any(_is_residual_phone(m.group()) for m in PHONE_PATTERN.finditer(text)):
        findings.append({"check": "residual_phone_pattern", "entity_type": "PHONE"})
    if any(_is_residual_ssn(m.group()) for m in GOVERNMENT_ID_PATTERN.finditer(text)):
        findings.append({"check": "residual_government_id_pattern", "entity_type": "GOVERNMENT_ID"})
    if any(_luhn_valid(match.group()) for match in CARD_PATTERN.finditer(text)):
        findings.append({"check": "residual_financial_identifier_pattern", "entity_type": "FINANCIAL_IDENTIFIER"})
    for match in IP_PATTERN.finditer(text):
        try:
            ipaddress.ip_address(match.group())
        except ValueError:
            continue
        findings.append({"check": "residual_ip_pattern", "entity_type": "IP_ADDRESS"})
        break
    return findings


def verify_redacted_text(
    original_text: str,
    redacted_text: str,
    original_entities: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Check known values and independent residual patterns without exposing values."""

    findings: list[dict[str, Any]] = []
    if not isinstance(original_text, str) or not isinstance(redacted_text, str):
        return {"status": "INCOMPLETE", "findings": [{"check": "invalid_text"}]}
    try:
        entities = list(original_entities)
    except TypeError:
        return {"status": "INCOMPLETE", "findings": [{"check": "invalid_entities"}]}

    for entity in entities:
        if not isinstance(entity, Mapping):
            findings.append({"check": "invalid_entity", "entity_type": "UNKNOWN"})
            continue
        start, end = entity.get("start"), entity.get("end")
        entity_type = str(entity.get("type", "UNKNOWN")).upper()
        if (
            not isinstance(start, int) or isinstance(start, bool)
            or not isinstance(end, int) or isinstance(end, bool)
            or start < 0 or end <= start or end > len(original_text)
        ):
            findings.append({"check": "invalid_entity_span", "entity_type": entity_type})
            continue
        sensitive_value = original_text[start:end]
        if sensitive_value and sensitive_value in redacted_text:
            findings.append({"check": "known_value_remaining", "entity_type": entity_type})
    findings.extend(_residual_findings(redacted_text))
    return {"status": "PASS" if not findings else "FAIL", "findings": findings}


def calculate_structure_score(original_text: str, redacted_text: str) -> float:
    """Check line boundaries and headings; format adapters need richer checks."""

    if not isinstance(original_text, str) or not isinstance(redacted_text, str):
        return 0.0

    orig_lines = len(original_text.splitlines())
    red_lines = len(redacted_text.splitlines())
    line_ratio = min(orig_lines, red_lines) / max(orig_lines, red_lines) if max(orig_lines, red_lines) > 0 else 1.0

    orig_headings = len(re.findall(r"(?m)^\s*#{1,6}\s", original_text))
    red_headings = len(re.findall(r"(?m)^\s*#{1,6}\s", redacted_text))
    heading_ratio = min(orig_headings, red_headings) / max(orig_headings, red_headings) if max(orig_headings, red_headings) > 0 else 1.0

    orig_nl = original_text.count("\n")
    red_nl = redacted_text.count("\n")
    nl_ratio = min(orig_nl, red_nl) / max(orig_nl, red_nl) if max(orig_nl, red_nl) > 0 else 1.0

    return (line_ratio + heading_ratio + nl_ratio) / 3.0


def verify_saved_artifact(
    artifact_ref: Any,
    text_reader: Callable[[Any], str] | None,
    original_text: str,
    redacted_entities: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Reopen the saved artifact using an injected format-specific reader."""

    if artifact_ref is None or not callable(text_reader):
        return {"status": "INCOMPLETE", "findings": [{"check": "artifact_verification_unavailable"}]}
    try:
        saved_text = text_reader(artifact_ref)
    except Exception:  # noqa: BLE001 - security boundary fails closed.
        return {"status": "INCOMPLETE", "findings": [{"check": "artifact_reopen_failed"}]}
    result = verify_redacted_text(original_text, saved_text, redacted_entities)
    if result["status"] != "PASS":
        return {
            "status": result["status"],
            "findings": [
                {"check": "saved_artifact_leakage", "entity_type": item.get("entity_type", "UNKNOWN")}
                for item in result["findings"]
            ],
        }
    return {"status": "PASS", "findings": []}
