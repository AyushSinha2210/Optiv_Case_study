# Member 5 & Member 4 Implementation Plan: PII Guard
### Cadence Financial Group — Cyber Strategy & AI Governance Case Study

**Author:** Tirth (Member 5: Orchestration, UI, Audit & Integration; also completing Member 4 Nancy's coding responsibilities)  
**Date:** 2026-10-13  
**Target Repository:** Optive PII Protection Case Study (`Optive_Case_study`)  
**Active Branch:** `feature/member5-integration`  
**Overall Implementation Status:** **100% COMPLETED**

---

## 1. Executive Summary & Responsibility Scope

This document specifies the concrete architecture, module contracts, implementation phases, and verification criteria for:
1. **Member 5 (Tirth):** End-to-end pipeline orchestration, lifecycle state machine, error handling, release gate authorization, audit logging, report generation, artifact access control, Streamlit UI, and integration/security test suites.
2. **Member 4 (Nancy - Coding Deliverables):** Deterministic synthetic PII demonstration fixture generator, sample manifests, evaluation metrics (precision, recall, F1, false negative rate), and export sanitization tests. *(Presentation slide deck is created separately by Nancy).*

---

## 2. Interface Contracts & Repository Ground Truth

The implementation conforms strictly to the canonical contracts in `docs/interfaces.md` and existing codebase schemas:

| Contract | Canonical Model | Source / Producer | Consumer | Sensitive Data Policy |
| :--- | :--- | :--- | :--- | :--- |
| **Contract A** | `ExtractedDocument` | `src/pii_guard/ingestion/extractor.py` (Ayush) | Detection / Orchestrator | Normalized immutable text with character offsets; fail-closed. |
| **Contract B** | `DetectionResult` | `src/pii_guard/detection/` (Avishi / Adapter) | Redaction / Orchestrator | Spans (`type`, `start`, `end`, `confidence`) mapped into `ExtractedDocument.text`. |
| **Contract C** | `RedactionResult` | `src/pii_guard/redaction/` (Yash / Adapter) | Orchestrator (Tirth) | `verification_status` (`PASS`/`FAIL`/`INCOMPLETE`), `release_allowed` (`bool`), opaque `artifact_ref`. |
| **Contract D** | `ProcessingReport` | `src/pii_guard/reporting/report_generator.py` (Tirth) | Client / Audit Trail | **Strictly metadata only.** Entity counts by category, timestamps, versions. Zero raw text. Zero PII. |

### Release Authorization Rule (Fail-Closed Barrier)
A document is **ONLY** released when:
$$\text{verification\_status} == \text{"PASS"} \quad \land \quad \text{release\_allowed} == \text{True}$$
All other combinations (`None`, `FAIL`, `INCOMPLETE`, missing fields, unexpected types, or upstream exceptions) strictly transition to `BLOCKED` or `FAILED` and prevent artifact retrieval.

---

## 3. Environment & Python Compatibility Strategy

- **System Executable:** Python 3.13.7 (`C:\Users\tirth\AppData\Local\Programs\Python\Python313\python.exe`)
- **Virtual Environment:** `.venv` created at project root using Python 3.13.7.
- **Dependency Analysis:**
  - `requirements.txt` installs cleanly on Python 3.13 (including Presidio 2.2.364, spaCy 3.8.16, Streamlit 1.65.0, pandas 3.0.6, PyPDF, pdfplumber, python-docx, python-pptx).
  - In `requirements-ingestion.txt`: `rapidocr-onnxruntime==1.4.4` declared `Requires-Python <3.13`. Tesseract OCR (`pytesseract`) is the primary production engine in `IngestionConfig` and runs independently of RapidOCR.
  - Standard unit, integration, reporting, evaluation, security, and synthetic fixture generation tests operate without requiring external Tesseract binaries or network downloads.
  - OCR tests requiring the system Tesseract binary are safely isolated so offline CI and environment constraints do not block testing.

---

## 4. Phase-by-Phase Implementation Checklist

### Phase 0: Repository Audit & Planning [COMPLETED]
- [x] Inspect Git status, active branch (`feature/member5-integration`), commit history.
- [x] Inspect existing directory structure and files.
- [x] Analyze Python versions and dependency resolution constraints.
- [x] Inspect Contract A implementation (`ExtractedDocument` in `src/pii_guard/ingestion/schemas.py`).
- [x] Author and commit `docs/member5_member4_implementation_plan.md`.

### Phase 1: Contract & State Foundation [COMPLETED]
- [x] Define canonical pipeline states in `src/pii_guard/orchestration/state.py`:
  - States: `RECEIVED`, `VALIDATED`, `EXTRACTED`, `DETECTED`, `REDACTED`, `VERIFIED`, `RELEASED`.
  - Terminal outcomes: `BLOCKED`, `FAILED`, `INCOMPLETE`.
  - Legal state transition validator and immutable transition record.
- [x] Define structured error hierarchy in `src/pii_guard/orchestration/errors.py`:
  - Categories: `INVALID_INPUT`, `UNSUPPORTED_FILE_TYPE`, `FILE_TOO_LARGE`, `DOCUMENT_READ_FAILED`, `EXTRACTION_FAILED`, `DETECTION_FAILED`, `REDACTION_FAILED`, `VERIFICATION_FAILED`, `RELEASE_BLOCKED`, `ARTIFACT_UNAVAILABLE`, `INTERNAL_PROCESSING_ERROR`.
  - Sanitized public error formatter (strips paths, stack traces, and document content).
- [x] Define Contract B (`DetectionResult`), Contract C (`RedactionResult`), and comprehensive `ProcessingResult` models.
- [x] Create unit tests in `tests/unit/test_state.py` and `tests/unit/test_errors.py`.
- [x] Verify with pytest (14 passing) and commit (`925dbf6`).

### Phase 2: Audit Subsystem [COMPLETED]
- [x] Implement sanitized audit event schema in `src/pii_guard/reporting/audit.py`.
- [x] Enforce field allowlisting and zero-leakage serialization.
- [x] Create unit tests in `tests/unit/test_audit.py` verifying canary PII strings are never serialized into audit records.
- [x] Verify with pytest (4 passing) and commit (`532a4a1`).

### Phase 3: Reporting Subsystem [COMPLETED]
- [x] Implement `src/pii_guard/reporting/report_generator.py`:
  - Contract D compliant machine-readable JSON generator.
  - Human-readable summary for console / UI display.
- [x] Implement `src/pii_guard/reporting/export.py` for sanitized JSON and CSV export.
- [x] Create unit tests in `tests/unit/test_reporting.py` verifying zero-leakage in all export formats.
- [x] Verify with pytest (6 passing) and commit (`3beed11`).

### Phase 4: Evaluation Metrics (Member 4) [COMPLETED]
- [x] Implement `src/pii_guard/reporting/metrics.py`:
  - Exact span & overlap matching rules.
  - True Positives (TP), False Positives (FP), False Negatives (FN).
  - Precision, Recall, F1 score, False Negative Rate (FNR).
  - Per-category metrics breakdown.
  - Zero-denominator guard (documented behavior returning 0.0 or 1.0 where appropriate).
- [x] Create evaluation tests in `tests/evaluation/test_metrics.py`.
- [x] Verify with pytest (10 passing) and commit (`4acb41f`).

### Phase 5: Synthetic Fixture Generator (Member 4) [COMPLETED]
- [x] Implement `demo_tools/generate_synthetic_samples.py`:
  - Deterministic PRNG seeded generation (`--seed`, `--output-dir`, `--manifest`).
  - Supported scenarios: email, phone, mixed PII, clean, repeated entities, unicode, empty, long document, malformed.
  - Plain text, docx, and synthetic test payloads.
  - Generates safe `demo_samples/manifest.json` with relative paths and entity metadata only.
- [x] Create `demo_samples/README.md` explaining reproducible generation and synthetic nature.
- [x] Create tests in `tests/unit/test_synthetic_generator.py`.
- [x] Run generator to produce reference demo fixtures and manifest.
- [x] Verify with pytest (4 passing) and commit (`dfdf812`).

### Phase 6: Orchestration Pipeline [COMPLETED]
- [x] Implement `src/pii_guard/orchestration/pipeline.py`:
  - Function: `process_document(file_path: str, options=None) -> ProcessingResult`.
  - Ingestion integration (`extract_document`).
  - Detection stage integration with fallback/mock adapter.
  - Redaction stage integration with fallback/mock adapter.
  - Strict release gate verification.
  - Sanitized audit recording for each stage transition.
- [x] Create mock-based integration tests in `tests/integration/test_orchestration.py`.
- [x] Verify with pytest (6 passing) and commit (`59f4046`).

### Phase 7: Artifact Access Control [COMPLETED]
- [x] Implement `src/pii_guard/orchestration/artifacts.py`:
  - Opaque token generation (`art-<uuid>`).
  - Controlled sandbox storage for redacted outputs.
  - Path traversal defense (`..` / absolute path rejection).
  - Authorization validation against `ProcessingResult.release_allowed`.
- [x] Create security tests in `tests/security/test_artifact_access.py`.
- [x] Verify with pytest (11 passing) and commit (`3f075a1`).

### Phase 8: Streamlit User Interface [COMPLETED]
- [x] Implement `app.py`:
  - Upload file interface with size and format guard.
  - Stage-by-stage pipeline progress indicator.
  - Extraction, detection, redaction, and verification status display.
  - Conditional release banner (green only on PASS; red blocked banner on FAIL/INCOMPLETE).
  - Category entity counts visualization.
  - Sanitized audit and report inspection tabs.
  - Gated download buttons for reports and authorized redacted artifacts.
- [x] Create UI smoke tests in `tests/unit/test_ui.py`.
- [x] Verify with pytest (6 passing) and commit (`6dd29d7`).

### Phase 9: Comprehensive Integration & Security Regression [COMPLETED]
- [x] Author `tests/security/test_release_gate.py` (fail-closed matrix: FAIL, INCOMPLETE, exceptions, tampering).
- [x] Author `tests/security/test_leakage.py` (canary injection across all outputs).
- [x] Run full test suite: unit, evaluation, integration, and security (69 passing tests).
- [x] Verify with pytest and commit (`4f7700c`).

### Phase 10: Documentation & Commit Log Finalization [COMPLETED]
- [x] Create `docs/architecture.md` (Operational planes, contracts, state machine, fail-closed gate).
- [x] Create `docs/security.md` (Threat model, security invariants, error sanitization, canary testing).
- [x] Create `docs/evaluation.md` (Bipartite matching, zero-denominator rules, metric definitions, fixture catalog).
- [x] Create `docs/demo_script.md` (Step-by-step presentation walkthrough, scenario scripts, demo FAQ).
- [x] Update `README.md` with Member 5 & Member 4 deliverables, quickstart, and DoD matrix.
- [x] Finalize `docs/member5_member4_commit_log.md`.
- [x] Commit documentation suite and provide comprehensive final engineering report.
