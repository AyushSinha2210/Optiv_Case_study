"""Validation rules that turn a regex hit into a plausible identifier.

A pattern match alone is not enough for identifier types: long digit runs
are common in ordinary business text, so each candidate must also pass a
format-level check where one exists.
"""

from __future__ import annotations

import re

_PAN_HOLDER_TYPES = frozenset("PCHFATBLJG")


def digits_only(text: str) -> str:
    return re.sub(r"\D", "", text)


def luhn_valid(number: str) -> bool:
    """Luhn checksum for payment-card-like digit strings (13 to 19 digits)."""
    if not number.isdigit() or not 13 <= len(number) <= 19:
        return False
    total = 0
    for index, char in enumerate(reversed(number)):
        digit = int(char)
        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def ssn_valid(value: str) -> bool:
    """US SSN structure AAA-GG-SSSS: area not 000/666/9xx, group not 00, serial not 0000."""
    parts = value.split("-")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        return False
    area, group, serial = parts
    area_n = int(area)
    if area_n == 0 or area_n == 666 or area_n >= 900:
        return False
    return int(group) != 0 and int(serial) != 0


def ipv4_valid(value: str) -> bool:
    parts = value.split(".")
    return len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)


def pan_valid(value: str) -> bool:
    """Indian PAN: 5 letters, 4 digits, 1 letter; 4th character is the holder-type code."""
    return len(value) == 10 and value[3] in _PAN_HOLDER_TYPES
