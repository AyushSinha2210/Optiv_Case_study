# Synthetic Demonstration Fixtures (Member 4 - Nancy)

This directory contains deterministic synthetic test and demonstration fixtures designed for the **Cadence Financial Group** PII Protection Case Study.

---

## 1. Safety & Privacy Mandate

- **100% Synthetic Data:** All names, email addresses, phone numbers, employee identifiers, and government numbers are strictly artificial.
- **Reserved Fictional Ranges:**
  - Phone numbers utilize reserved `555-01xx` fictional exchanges.
  - Email addresses use RFC 2606 reserved domains (`example.com`, `example.org`, `.test`).
  - Government identification strings use the unassigned `000-xx-xxxx` range reserved by the Social Security Administration.
- **Zero Production Dependency:** This fixture generator is fully decoupled from production ingestion, detection, and redaction pipelines.

---

## 2. Generating Fixtures & Setting Seeds

To regenerate all fixtures deterministically from the repository root:

```bash
# Default deterministic generation (seed = 42)
python demo_tools/generate_synthetic_samples.py

# Custom deterministic seed
python demo_tools/generate_synthetic_samples.py --seed 1337

# Custom output directory
python demo_tools/generate_synthetic_samples.py --output-dir custom_samples --seed 42
```

The generator is idempotent: running with the identical seed produces identical character byte streams.

---

## 3. Scenarios Catalog (`manifest.json`)

| Fixture ID | Scenario | File Type | Key Characteristics | Expected Categories |
| :--- | :--- | :---: | :--- | :--- |
| `synth-001` | `scenario_email` | `.txt` | Plain text business notice with 2 synthetic email addresses. | `EMAIL` |
| `synth-002` | `scenario_phone` | `.txt` | Support roster with 2 synthetic phone numbers. | `PHONE` |
| `synth-003` | `scenario_mixed_pii` | `.txt` | Multi-category record (Employee ID, Email, Phone, SSN). | `EMPLOYEE_ID`, `EMAIL`, `PHONE`, `GOVERNMENT_ID` |
| `synth-004` | `scenario_clean_no_pii` | `.txt` | Technical architecture specifications with zero personal data. | *(None)* |
| `synth-005` | `scenario_repeated_entities` | `.txt` | Single synthetic email repeated across 4 separate paragraphs. | `EMAIL` |
| `synth-006` | `scenario_multi_category_docx`| `.docx` | Word document containing interleaved tables and headers. | `EMPLOYEE_ID`, `EMAIL`, `PHONE` |
| `synth-007` | `scenario_unicode_international` | `.txt` | Accented French and German text and Japanese script. | `EMAIL`, `PHONE` |
| `synth-008` | `scenario_empty` | `.txt` | 0-byte document testing fail-closed validation defenses. | *(None)* |
| `synth-009` | `scenario_long_document` | `.txt` | 20-paragraph document with sparse entities to test throughput. | `EMAIL` |
| `synth-010` | `scenario_unsupported_malformed`| `.xyz` | Arbitrary binary payload verifying format rejection. | *(None)* |

---

## 4. Running Automated Tests Against Demo Fixtures

Automated tests in `tests/unit/test_synthetic_generator.py` verify that:
1. Running with the same seed produces identical byte streams.
2. The manifest conforms to the required schema.
3. Relative paths are safe and contain no path traversal characters (`..`).
4. All generated data is synthetic and free from sensitive corporate information.
