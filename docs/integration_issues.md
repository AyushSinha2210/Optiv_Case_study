# PII Guard: Integration Issues Tracker & Root-Cause Analysis

**Branch:** `fix/pii-guard-integration-audit`  
**Base Commit:** `2dc12882e9cd0214ecba9aad8ff516a9c0fce9a3`  

---

## Issue Registry

| Issue ID | Severity | Affected Module | Root Cause Summary | Status | Commit SHA |
| :---: | :---: | :--- | :--- | :---: | :---: |
| **INT-001** | CRITICAL | Detection | Merge conflict markers in detection package (`__init__.py`, `classifier.py`, `pattern_detector.py`, `validators.py`) | VERIFIED | `215623c` |
| **INT-002** | HIGH | Detection | NameError (`ner_backend` undefined) in `PIIDetector.__init__` and missing Member 2 detector logic in `detector.py` | VERIFIED | `215623c` |
| **INT-003** | CRITICAL | Redaction | Merge conflict markers in redaction package (`__init__.py`, `redactor.py`, `service.py`) | VERIFIED | `cfe21bc` |
| **INT-004** | HIGH | Redaction / Orchestration | Alignment between `pipeline.py` and `service.py` for `artifact_manager` and `simulate_verification_failure` | VERIFIED | `cfe21bc` |
| **INT-005** | CRITICAL | Tests (Detection) | Merge conflict markers on lines 97 and 373 of `tests/test_detection.py` causing syntax errors during test discovery | VERIFIED | `215623c` |
| **INT-006** | MEDIUM | Evaluation | Merge conflict markers in `evaluation/build_ground_truth.py` and `evaluation/ground_truth.jsonl` | VERIFIED | `215623c` |
| **INT-007** | MEDIUM | Documentation | Merge conflict markers in `README.md`, `docs/detection.md`, and `docs/security.md` | VERIFIED | `9f6f998` |
| **INT-008** | LOW | Ingestion | Host-dependent OCR binary check causing failure on systems without Tesseract installed on OS PATH | VERIFIED | `3217a16` |
| **INT-009** | MEDIUM | Frontend / UI | Ensure Streamlit UI in `app.py` has full observability of backend execution stages and demonstration modes | VERIFIED | `50cb4e7` |
| **INT-010** | HIGH | Detection / Verification | Restrictive phone regex and synthetic SSN format caused unredacted residuals and blocked release | VERIFIED | `6b55ff5` |
| **INT-011** | HIGH | Frontend / API | Implement modern React TypeScript web frontend, FastAPI HTTP adapter, live inspector, diff view, and AI copilot | VERIFIED | `17d83fa` |

---

## Detailed Issue Analysis & Resolution Log

### INT-001: Detection Module Merge Conflict Markers
* **Severity:** CRITICAL
* **Affected Files:**
  * `src/pii_guard/detection/__init__.py`
  * `src/pii_guard/detection/classifier.py`
  * `src/pii_guard/detection/pattern_detector.py`
  * `src/pii_guard/detection/validators.py`
* **Observable Symptoms:** Importing `pii_guard.detection` raises `SyntaxError: unterminated triple-quoted string literal` or syntax errors on `<<<<<<< HEAD`. Test discovery fails for `tests/test_redaction.py`, and orchestration pipeline fails at `DETECTED` stage.
* **Root Cause:** Incomplete merge in commit `ac5eac6` left conflict markers in source code.
* **Expected Behavior:** Modules import cleanly, `PRECEDENCE.get(c.type, 0)` is safe, and `_EMPLOYEE` regex matches both `EMP-` and `CAD-EMP-` formats.
* **Minimum Safe Fix:** Remove conflict markers, retain Member 2's safe precedence and pattern definitions.
* **Regression Tests:** `tests/test_detection.py` (60 passed).
* **Commit SHA:** `215623c`
* **Status:** VERIFIED

---

### INT-002: NameError & Missing Logic in `detector.py`
* **Severity:** HIGH
* **Affected File:** `src/pii_guard/detection/detector.py`
* **Observable Symptoms:** `PIIDetector()` raises `NameError: name 'ner_backend' is not defined`. Member 2's validation and NER classification logic are bypassed.
* **Root Cause:** `detector.py` was replaced with an incomplete snippet that assigned `self.ner_backend = ner_backend` without taking `ner_backend` as an argument.
* **Expected Behavior:** `detect_pii(document, ner_backend=None, options=None, **kwargs)` performs full pattern and NER detection; `PIIDetector` wrapper cleanly delegates to `detect_pii`.
* **Minimum Safe Fix:** Restore Member 2's `detect_pii` logic and provide a clean `PIIDetector` class accepting optional `ner_backend` and `confidence_threshold`.
* **Regression Tests:** `tests/test_detection.py`, `tests/integration/test_pipeline_e2e.py`.
* **Commit SHA:** `215623c`
* **Status:** VERIFIED

---

### INT-003: Redaction Module Merge Conflict Markers
* **Severity:** CRITICAL
* **Affected Files:**
  * `src/pii_guard/redaction/__init__.py`
  * `src/pii_guard/redaction/redactor.py`
  * `src/pii_guard/redaction/service.py`
* **Observable Symptoms:** Syntax errors when importing `pii_guard.redaction`.
* **Root Cause:** Merge conflict markers committed into redaction files.
* **Expected Behavior:** Redaction package exports all Contract C models, functions (`apply_redactions`, `redact_text`, `validate_spans`, `redact_and_validate`), and `Redactor` class cleanly.
* **Minimum Safe Fix:** Cleanly resolve all conflict markers across the 3 files.
* **Regression Tests:** `tests/test_redaction.py` (10 passed).
* **Commit SHA:** `cfe21bc`
* **Status:** VERIFIED

---

### INT-004: Parameter Alignment between `pipeline.py` and `service.py`
* **Severity:** HIGH
* **Affected Files:** `src/pii_guard/redaction/service.py` & `src/pii_guard/redaction/redactor.py`
* **Observable Symptoms:** TypeError on unexpected keyword argument or missing artifact verification when `artifact_manager` is supplied by the pipeline.
* **Root Cause:** Member 3's `service.py` originally expected format-specific reader functions, while Member 5's orchestrator provides `artifact_manager` and sandbox storage.
* **Expected Behavior:** `redact_and_validate` seamlessly supports both Member 3's standalone test parameters (`artifact_ref`, `artifact_text_reader`) and Member 5's orchestration parameters (`artifact_manager`, `simulate_verification_failure`).
* **Minimum Safe Fix:** Integrate the adapter block inside `service.py` and export it through `redactor.py` and `__init__.py`.
* **Regression Tests:** `tests/test_redaction.py`, `tests/integration/test_pipeline_e2e.py`, `tests/security/test_fail_closed_gate.py`.
* **Commit SHA:** `cfe21bc`
* **Status:** VERIFIED

---

### INT-005: Detection Test Discovery SyntaxError
* **Severity:** CRITICAL
* **Affected File:** `tests/test_detection.py`
* **Observable Symptoms:** `pytest` terminates with `SyntaxError: invalid syntax` on line 97 of `test_detection.py`.
* **Root Cause:** Conflict markers on lines 97-100 and 373-396.
* **Expected Behavior:** Pytest collects and executes all 60 detection tests successfully.
* **Minimum Safe Fix:** Remove conflict markers, retaining both `CAD-EMP-83563` parameterized fixture and edge-case tests.
* **Regression Tests:** `tests/test_detection.py` (60 passed).
* **Commit SHA:** `215623c`
* **Status:** VERIFIED

---

### INT-006: Evaluation Ground Truth Conflict Markers
* **Severity:** MEDIUM
* **Affected Files:** `evaluation/build_ground_truth.py`, `evaluation/ground_truth.jsonl`
* **Observable Symptoms:** Running `python -m evaluation.build_ground_truth` fails on conflict markers; parsing `ground_truth.jsonl` fails with invalid JSON.
* **Root Cause:** Conflict markers on lines 46-54 of `build_ground_truth.py` and lines 23-31 of `ground_truth.jsonl`.
* **Expected Behavior:** All 28 synthetic ground-truth evaluation documents parse cleanly.
* **Minimum Safe Fix:** Remove conflict markers and retain all 28 ground-truth test cases.
* **Regression Tests:** `tests/evaluation/test_metrics.py`, `tests/evaluation/test_ground_truth.py`.
* **Commit SHA:** `215623c`
* **Status:** VERIFIED

---

### INT-007: Documentation Merge Conflict Markers
* **Severity:** MEDIUM
* **Affected Files:** `README.md`, `docs/detection.md`, `docs/security.md`
* **Observable Symptoms:** Markdown documents contain conflicting diff text and broken formatting.
* **Root Cause:** Merge conflict markers committed into docs during commit `ac5eac6`.
* **Expected Behavior:** Clean, coherent, and complete documentation accurately reflecting the repository architecture and team roles.
* **Minimum Safe Fix:** Unify sections, keeping team rosters, architecture diagrams, DoD tables, and module notes.
* **Regression Tests:** Clean grep search for conflict markers across entire repo.
* **Commit SHA:** `9f6f998`
* **Status:** VERIFIED

---

### INT-008: Host Environment Dependency for Scanned PDF Tests
* **Severity:** LOW
* **Affected File:** `tests/test_ingestion.py`
* **Observable Symptoms:** 3 tests (`test_extract_scanned_pdf`, `test_extract_rotated_scanned_pdf`, `test_extract_mixed_pdf`) fail on Windows machines where Tesseract is not installed on the system PATH.
* **Root Cause:** Tesseract engine raises error or returns empty string when OCR binary is missing on host.
* **Expected Behavior:** Tests should detect whether Tesseract binary is available on the system PATH; if absent, gracefully skip with an informative reason rather than failing.
* **Minimum Safe Fix:** Add `shutil.which("tesseract")` check in `test_ingestion.py` for scanned PDF tests that require the Tesseract executable.
* **Regression Tests:** `tests/test_ingestion.py` (17 passed, 3 skipped gracefully).
* **Commit SHA:** `3217a16`
* **Status:** VERIFIED

---

### INT-009: Frontend Live Observability & Demonstration
* **Severity:** MEDIUM
* **Affected Files:** `app.py`, `tests/unit/test_ui.py`
* **Observable Symptoms:** Presenter needs an interactive walkthrough covering all 7 stages, real telemetry, verification outcomes, and failure simulations.
* **Expected Behavior:** Streamlit app allows selecting synthetic scenarios from `demo_samples`, shows real execution history, metrics, and gated download controls.
* **Minimum Safe Fix:** Enhance `app.py` with scenario picker from `demo_samples`, detailed stage telemetry display, and verification controls; add unit tests for demo scenario coverage.
* **Regression Tests:** `tests/unit/test_ui.py` (7 passed).
* **Commit SHA:** `50cb4e7`
* **Status:** VERIFIED

---

### INT-010: Investigation and Resolution of Residual Verification Failure
* **Severity:** HIGH
* **Affected Files:** `src/pii_guard/detection/pattern_detector.py`, `demo_tools/generate_synthetic_samples.py`, `demo_samples/fixtures/`
* **Observable Symptoms:** Documents containing phone numbers and synthetic SSNs (e.g. `02_synthetic_phone.txt`, `03_mixed_pii.txt`, `06_multi_category.docx`, `07_unicode_international.txt`) returned `workflow_status="blocked"`, `verification_status="FAIL"`, `release_allowed=False` with error `"Verification re-scan detected residual PII: release is blocked"`.
* **Root Cause:**
  1. `pattern_detector.py`'s `_PHONE` regex was strictly rigid, matching only 3-3-4 digit groupings (`\(\d{3}\)[ .-]?\d{3}[ .-]?\d{4}`). It failed to match 3-4-4 synthetic phone numbers (e.g., `(555) 0186-9935`) and international numbers with 2-digit city codes (e.g., `+41 22 555 0199`).
  2. Because the detector missed those phone numbers, they were left unmasked. Member 3's independent verification `PHONE_PATTERN` correctly identified them as residual PII leaks, triggering the fail-closed release gate barrier.
  3. In `03_mixed_pii.txt`, the synthetic SSN generated by Member 4 used area code `000` (`000-87-1434`), which is rejected as non-SSN by `validators.ssn_valid`. Consequently, `detect_pii` missed it, redaction skipped it, and `verifier.py`'s `GOVERNMENT_ID_PATTERN` flagged it as residual PII.
* **Minimum Safe Fix:**
  1. Updated `_PHONE` regex in `pattern_detector.py` to recognize 2-4 digit groupings while keeping near-miss non-PII boundary guards intact.
  2. Updated `_rand_ssn` in `generate_synthetic_samples.py` to generate structurally valid SSN area codes (avoiding 000, 666, and 900+), ensuring detection and independent verification agree on valid identifiers.
* **Regression Tests:** Pytest full test suite (169 passed, 3 skipped), all 10 demo fixtures processed through pipeline with 100% verified release authorization.
* **Commit SHA:** `6b55ff5`
* **Status:** VERIFIED

---

### INT-011: React/TypeScript Web Frontend, FastAPI HTTP Adapter, and AI Copilot
* **Severity:** HIGH
* **Affected Files:** `server.py`, `frontend/`, `tests/unit/test_api_server.py`, `.gitignore`
* **Observable Symptoms:** Streamlit Python frontend does not satisfy the requirement for a modern, production-grade JavaScript/TypeScript web interface, live execution inspector, comparison diff view, and AI copilot.
* **Root Cause:** Original presentation layer was implemented in Python (Streamlit) without an explicit REST HTTP API.
* **Minimum Safe Fix:**
  1. Created a clean, minimal FastAPI HTTP adapter (`server.py`) delegating directly to existing pipeline entry points (`process_document`, `extract_document`, `detect_pii`, `get_default_artifact_manager`, `generate_report`, `get_global_audit_trail`).
  2. Implemented a React + TypeScript + Vite web application in `frontend/` featuring:
     - Live Execution Inspector with 7-stage lifecycle stepper and step-by-step durations.
     - Document Comparison View with highlighted PII spans and classified entity inventory.
     - AI Security & Governance Copilot answering questions about release decisions, taxonomy, and policy.
     - Sanitized Audit Ledger with Contract D JSON/CSV exports and gated artifact download buttons.
  3. Added comprehensive automated tests in `tests/unit/test_api_server.py`.
* **Regression Tests:** `tests/unit/test_api_server.py` (6 passed), `npm run build` in `frontend/` (built in < 1s with 0 errors).
* **Commit SHA:** `17d83fa`
* **Status:** VERIFIED

