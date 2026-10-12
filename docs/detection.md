# PII Detection & Classification (Member 2: Avishi Sharma)

Locates PII in `ExtractedDocument.text` and returns classified spans (Contract B).

## Public API

```python
from pii_guard.detection import detect_pii, load_spacy_backend

result = detect_pii(extracted_document, ner_backend=None)   # -> DetectionResult
```

- `extracted_document` needs `document_id`, `text`, `extraction_status` (Contract A).
- `ner_backend=None` disables PERSON detection and adds a `NER_UNAVAILABLE` warning.
- `load_spacy_backend()` returns a spaCy backend if `spacy` and `en_core_web_sm` are installed, otherwise `None`.
- Raises `DetectionInputError` for a failed extraction, a missing `document_id`, or an unknown status. This is fail-closed: a refused run is never reported as "no PII".

## Taxonomy

| Type | Method | Confidence | Validation |
| :--- | :--- | :---: | :--- |
| `EMAIL` | regex | 0.98 | local@domain.tld shape |
| `GOVERNMENT_ID` (US SSN) | regex | 0.97 | area not 000/666/9xx, group not 00, serial not 0000 |
| `GOVERNMENT_ID` (IN PAN) | regex | 0.95 | 5 letters, 4 digits, 1 letter; 4th letter is a holder-type code |
| `FINANCIAL_IDENTIFIER` | regex | 0.99 | 13–19 digits, Luhn checksum |
| `EMPLOYEE_ID` | regex | 0.95 | `EMP-` + 5 digits (agreed format; to confirm with Member 1/5) |
| `IP_ADDRESS` | regex | 0.90 | IPv4 octets 0–255 |
| `PHONE` | regex | 0.80 | 10 digits in 3-3-4 or 5-5 grouping, optional `+CC` |
| `PERSON` | NER adapter | backend score | optional, see below |
| `ADDRESS` | not implemented | — | would need a NER label or address parser |

Plain digit runs are **not** classified as IDs. A card number needs a passing Luhn check, and a 13-digit order number fails it.

## Overlap and precedence

When spans overlap, the higher-precedence type wins: GOVERNMENT_ID / FINANCIAL_IDENTIFIER (5), EMPLOYEE_ID / EMAIL (4), IP_ADDRESS (3), PHONE (2), PERSON / ADDRESS (1). Ties go to the longer span, then higher confidence, then earlier start. Results are deterministic. Each overlap resolution adds an `OVERLAP_RESOLVED` warning with a count only.

Example: in `10.0.0.1@example.test` the IPv4-looking local part is dropped and the span is kept as `EMAIL`.

## Offsets and page safety

- Offsets are zero-based and end-exclusive into the exact `text`. The text is never normalized.
- Pages are separated by `\f`. Pattern and NER spans cannot cross a page boundary. NER runs one page at a time.

## NER adapter

The adapter accepts any callable `text -> [(label, start, end, score)]`, so the backend can be swapped and tests can inject fakes. Only `PERSON` is mapped. `LOC`/`GPE` are not mapped to `ADDRESS`, because a city is not an address.

spaCy does not give calibrated per-entity scores, so the spaCy backend uses a fixed 0.75. Presidio is not wired in yet.

## Warnings

Warnings are safe, metadata-only records: `code` and `message`. Messages never contain document text or matched values.

| Code | Meaning |
| :--- | :--- |
| `NER_UNAVAILABLE` | No NER backend; PERSON not detected |
| `UPSTREAM_PARTIAL_EXTRACTION` | Extraction was partial; coverage may be incomplete |
| `EMPTY_TEXT` | Nothing to scan |
| `OVERLAP_RESOLVED` | Overlapping candidates resolved by precedence (count) |
| `INVALID_SPAN_DROPPED` | Candidate failed bounds or page checks and was dropped (count) |

## Evaluation

Ground truth is synthetic. Annotations are written as `[[TYPE|value]]` in `evaluation/build_ground_truth.py`, which computes offsets into `evaluation/ground_truth.jsonl`. A test checks that every offset matches its value and that the JSONL is in sync with the source.

```bash
python -m evaluation.build_ground_truth   # regenerate ground truth
python -m evaluation.metrics              # precision / recall / F1 table
python -m evaluation.metrics --no-ner     # pattern-only, force-skip NER
```

Matching is exact span plus type. A zero denominator is reported as `n/a`. Types that need NER are excluded when no backend is installed, and the report says so.

### Current numbers and what they mean

- 22 synthetic documents, 18 scored entities (pattern types), 3 PERSON entities not scored.
- Pattern types score 1.000 precision and recall on this corpus.
- **This is not a generalisation result.** The regexes and the corpus were written in the same pass, so the corpus is not a hold-out. A result is only meaningful once a separately written hold-out set exists.
- PERSON is unmeasured until a NER backend is installed and run.

## Known limitations

- Phone format covers common US/IN layouts only. A 10-digit run with no separators is matched; a 7-digit local number is not.
- IPv4 matching also fires on version-like strings that happen to be four valid octets (e.g. `1.2.3.4`). Precision on this class is unmeasured.
- The `EMP-` employee ID format is an assumption and must be confirmed against the agreed use case.
- ADDRESS is not detected.
- Context-free rules cannot tell a real SSN from a test value that passes the structural check.
- NER is optional and not installed in the current environment, so PERSON recall is unknown.

## Tests

```bash
pytest -q tests/test_detection.py
```

No network, API keys or NER model are needed. Covers validators, per-type positives and near-misses, precedence, offsets, page safety, fail-closed inputs, the NER fallback, and ground-truth consistency.
