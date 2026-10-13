"""Build evaluation/ground_truth.jsonl from marked-up synthetic text.

Annotation format: each PII value is wrapped as [[TYPE|value]]. This script
removes the markers and records zero-based, end-exclusive offsets of each value
in the resulting plain text. All values are invented (example.test emails,
555-01xx phone numbers, 192.0.2.0/24 documentation IPs, fictional names).

Run from the repository root:
    python -m evaluation.build_ground_truth
"""

from __future__ import annotations

import json
import re
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent / "ground_truth.jsonl"

_TAG = re.compile(r"\[\[([A-Z_]+)\|(.*?)\]\]", re.DOTALL)

# Negative cases (no PII) and near-misses are included on purpose.
CORPUS: list[tuple[str, str]] = [
    ("det-001", "Please send the revised statement to [[EMAIL|alex.rivera@example.test]] or call [[PHONE|+1 (415) 555-0132]] before Friday."),
    ("det-002", "The quarterly risk committee meets on the second Tuesday. Agenda items are listed in the shared calendar."),
    ("det-003", "Applicant SSN is [[GOVERNMENT_ID|123-45-6789]]; internal reference [[EMPLOYEE_ID|EMP-10482]] is attached to the onboarding file."),
    ("det-004", "Card on file [[FINANCIAL_IDENTIFIER|4111 1111 1111 1111]] expires next year. Do not store it in plain text."),
    ("det-005", "Batch reference 4111 1111 1111 1112 was rejected by the reconciliation job."),
    ("det-006", "Test value 666-12-3456 and short form 123-45-678 are not valid identifiers."),
    ("det-007", "Connection from [[IP_ADDRESS|192.0.2.44]] was logged at 09:14 UTC."),
    ("det-008", "Release 2.10.3 was deployed on 2026-10-12 under change ticket CHG-2231, build 1.2.3."),
    ("det-009", "PAN on the application form is [[GOVERNMENT_ID|ABCPE1234F]] as shown in the KYC scan."),
    ("det-010", "Order 1234567890123 shipped; tracking code TRK-889900."),
    ("det-011", "[[PERSON|Alex Example]] ([[EMPLOYEE_ID|EMP-20011]]) can be reached at [[EMAIL|alex@example.test]] or [[PHONE|555-013-7788]]."),
    ("det-012", "Owner account [[EMAIL|10.0.0.1@example.test]] was flagged by the mail filter."),
    ("det-013", "Reference 2026-10-12 and extension 0132 only, no contact details here."),
    ("det-014", "Page one contact: [[EMAIL|ops.team@example.test]]\fPage two contact: [[PHONE|5550139245]]."),
    ("det-015", "Q3 revenue grew 12.5 percent; this memo contains no customer data."),
    ("det-016", "Reach me at [[EMAIL|ops.team@example.test]], or [[PHONE|+91 98765 43210]]."),
    ("det-017", "Holder code check: ABCDE1234F is not a valid holder type."),
    ("det-018", "Gateway [[IP_ADDRESS|198.51.100.7]] and backup [[IP_ADDRESS|203.0.113.19]] are documented in the runbook."),
    ("det-019", ""),
    ("det-020", "Prepared by [[PERSON|Julian Thorne]] for the audit committee."),
    ("det-021", "Escalate to [[PERSON|Priya Raman]] at [[EMAIL|priya.raman@example.test]] if the batch fails."),
    ("det-022", "Build 12345 and ticket 67890 were merged at 10:30."),
<<<<<<< HEAD
=======
    ("det-023", "Customer [[PERSON|Maya Lindqvist]] asked us to update the email to [[EMAIL|maya.l@example.test]]."),
    ("det-024", "Call the branch on [[PHONE|555-014-2280]] between 9 and 5."),
    ("det-025", "Refund card [[FINANCIAL_IDENTIFIER|4000 0000 0000 0002]] was issued to [[PERSON|Ravi Kumar]]."),
    ("det-026", "Server [[IP_ADDRESS|192.0.2.201]] restarted; ticket 1.2.3 remains open."),
    ("det-027", "Employee [[EMPLOYEE_ID|EMP-30051]] requested access; no contact details included."),
    ("det-028", "Invoice dated 2026-10-12 totals 4500 rupees; no personal data."),
>>>>>>> origin/feature/member5-integration
]


def render(markup: str) -> tuple[str, list[dict]]:
    """Strip markers and return (plain_text, entities with offsets)."""
    pieces: list[str] = []
    entities: list[dict] = []
    cursor = 0  # position in markup
    length = 0  # length of plain text emitted so far

    for match in _TAG.finditer(markup):
        plain = markup[cursor:match.start()]
        pieces.append(plain)
        length += len(plain)

        value = match.group(2)
        start = length
        pieces.append(value)
        length += len(value)
        entities.append({"type": match.group(1), "start": start, "end": length, "value": value})
        cursor = match.end()

    pieces.append(markup[cursor:])
    return "".join(pieces), entities


def build() -> int:
    records = []
    for doc_id, markup in CORPUS:
        text, entities = render(markup)
        for entity in entities:
            assert text[entity["start"]:entity["end"]] == entity["value"], doc_id
        records.append({"doc_id": doc_id, "text": text, "entities": entities})

    with open(OUTPUT, "w", encoding="utf-8", newline="\n") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return len(records)


if __name__ == "__main__":
    count = build()
    print(f"Wrote {count} synthetic documents to {OUTPUT}")
