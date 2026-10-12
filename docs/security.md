# Member 3 security notes

Member 3 owns deterministic redaction, verification, leakage testing,
structure-preservation checks, and the fail-closed release gate.

## Rules

- Detection offsets are zero-based and end-exclusive into the exact extracted text.
- Unknown, invalid, out-of-range, and overlapping spans are rejected.
- Replacements are applied from the highest offset to the lowest.
- Findings never contain raw document text, matched values, or source snippets.
- Verification checks both known detected values and independent residual patterns.
- The saved artifact must be reopened by a format-specific reader before `PASS`.
- Missing or failed verification means `release_allowed=False`.
- Only synthetic values may be committed to tests and fixtures.

## Saved artifact verification

`redact_and_validate()` accepts `artifact_ref` and `artifact_text_reader`. The
reader must reopen the actual saved output and extract its text. For PDF,
covering text with a black rectangle is not sufficient: the original text must
not remain selectable or extractable. PDF/DOCX/PPTX adapters should also check
supported hidden layers, comments, and metadata.

The current module intentionally does not pretend to implement format-specific
export/redaction adapters. It provides the security boundary where those
adapters are connected.

## Structure score

The included score checks line boundaries and heading counts. It is not a
complete PDF, DOCX, or PPTX layout score. Format adapters must add page,
paragraph, table, or slide checks before claiming full structure preservation.

## Known limitation

No verifier can prove that every possible PII value was detected. Missed names,
addresses, or unusual identifiers remain residual risk and must be documented.

## Test command

```bash
pytest -q tests/test_redaction.py
```
