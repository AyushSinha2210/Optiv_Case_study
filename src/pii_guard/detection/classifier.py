"""Deterministic overlap resolution and label precedence.

When candidates overlap, the higher-precedence type wins. Ties are broken by
longer span, then higher confidence, then earlier start, then type name.
The same input always yields the same output.
"""

from __future__ import annotations

from .schemas import Candidate

# Higher number wins. Validated identifiers outrank generic formats, which
# outrank contextual NER. So an email whose local part looks like a name is
# kept as EMAIL, and an IPv4-looking local part inside an email is kept as EMAIL.
PRECEDENCE: dict[str, int] = {
    "GOVERNMENT_ID": 5,
    "FINANCIAL_IDENTIFIER": 5,
    "EMPLOYEE_ID": 4,
    "EMAIL": 4,
    "IP_ADDRESS": 3,
    "PHONE": 2,
    "PERSON": 1,
    "ADDRESS": 1,
}


def resolve_overlaps(candidates: list[Candidate]) -> tuple[list[Candidate], int]:
    """Return (non-overlapping candidates sorted by start, number of candidates dropped)."""
    ordered = sorted(
        candidates,
        key=lambda c: (
            -PRECEDENCE[c.type],
            -(c.end - c.start),
            -c.confidence,
            c.start,
            c.type,
        ),
    )
    accepted: list[Candidate] = []
    dropped = 0
    for candidate in ordered:
        if any(candidate.start < kept.end and kept.start < candidate.end for kept in accepted):
            dropped += 1
            continue
        accepted.append(candidate)
    accepted.sort(key=lambda c: (c.start, c.end))
    return accepted, dropped
