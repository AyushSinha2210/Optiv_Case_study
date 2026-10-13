# PII Guard: System Integration Audit & Architecture Verification

**Project:** Optiv Case Study — PII Guard  
**Client:** Cadence Financial Group  
**Auditor / Integration Engineer:** Principal Integration & Security Specialist  
**Target Repository:** `AyushSinha2210/Optive_Case_study`  
**Repair Branch:** `fix/pii-guard-integration-audit`  
**Base Commit:** `2dc12882e9cd0214ecba9aad8ff516a9c0fce9a3` (`origin/main`)  

---

## 1. Executive Summary

This architecture verification audit evaluates the operational integrity, inter-module contracts, security boundaries, and runtime observability of **PII Guard**, an enterprise privacy-preserving document processing pipeline built for Cadence Financial Group. 

The pipeline guarantees that before business artifacts reach downstream Large Language Model (LLM) agents or client download channels, all Sensitive Personal Identifiable Information (PII) is classified, deterministically redacted, independently verified, and controlled by a fail-closed dual-key release gate.

---

## 2. Module Ownership & Architectural Boundaries

In accordance with architectural specifications, module responsibilities are partitioned into strictly bounded domains:

| Module | Team Member | Primary Deliverables & Owned Paths | Consumed Inputs | Produced Output |
| :--- | :--- | :--- | :--- | :--- |
| **Ingestion** | **Member 1: Ayush Sinha** | `src/pii_guard/ingestion/`<br>`tests/test_ingestion.py`<br>`docs/ingestion.md` | Raw uploaded document (`.pdf`, `.docx`, `.pptx`, `.txt`) | **Contract A:** `ExtractedDocument` |
| **Detection** | **Member 2: Avishi Sharma** | `src/pii_guard/detection/`<br>`tests/test_detection.py`<br>`evaluation/` | `ExtractedDocument` | **Contract B:** `DetectionResult` |
| **Redaction** | **Member 3: Yash Jhinkwan** | `src/pii_guard/redaction/`<br>`tests/test_redaction.py`<br>`docs/security.md` | `ExtractedDocument` + `DetectionResult` | **Contract C:** `RedactionResult` |
| **Fixtures / Evaluation** | **Member 4: Nancy / Anshika** | `demo_tools/`<br>`demo_samples/`<br>`src/pii_guard/reporting/metrics.py`<br>`tests/evaluation/` | Ground-truth annotations & predictions | Bipartite matching metrics (Precision, Recall, F1) |
| **Orchestration & UI** | **Member 5: Tirth Bora** | `src/pii_guard/orchestration/`<br>`src/pii_guard/reporting/`<br>`app.py`<br>`tests/unit/`, `tests/integration/`, `tests/security/` | Document file path, options, audit trail | **Contract D:** `ProcessingReport` + `ProcessingResult` |

---

## 3. Verified End-to-End Call Chain

The complete verified execution sequence flows monotonically through 7 stages:

```
[ User Upload via Streamlit / CLI / API ]
                   │
                   ▼
  Stage 1: Pipeline Initialization (RECEIVED)
     - Validate input file path exists and is not a directory
     - Verify file extension in [.pdf, .docx, .pptx, .txt, .text]
     - Enforce file size limit <= 50 MB and > 0 bytes
                   │
                   ▼
  Stage 2: Pre-Flight Validation (VALIDATED)
     - Magic byte sniffing (reject renamed binaries / scripts)
     - Zip-bomb defense (compression ratio <= 100:1)
     - Encrypted PDF protection (detect and fail closed)
                   │
                   ▼
  Stage 3: Text & Structure Extraction (EXTRACTED)
     - Invoke format adapter (PDFAdapter, DocxAdapter, PptxAdapter, TxtAdapter)
     - Preserve visual reading order and layout offsets
     - Run OCR fallback if digital text is absent (< 10 chars / page)
     - Single-pass Unicode NFC normalizer
     - Produces Contract A: ExtractedDocument
                   │
                   ▼
  Stage 4: PII Detection & Classification (DETECTED)
     - Pattern detectors (regex rules with checksum & format validators)
     - Optional NER backend for PERSON entities
     - Overlap resolution via deterministic label precedence
     - Produces Contract B: DetectionResult
                   │
                   ▼
  Stage 5: Deterministic Redaction (REDACTED)
     - Right-to-left offset replacement to avoid index shifting
     - Replacement token formatting ([REDACTED_TYPE])
     - Safe error handling for invalid or overlapping bounds
                   │
                   ▼
  Stage 6: Independent Verification Re-Scan (VERIFIED)
     - Re-scan redacted text for known detected values and residual PII patterns
     - Reopen persisted sandbox artifact via format reader (if artifact_manager provided)
     - Compute layout structure retention score (>= 1.0)
     - Produces Contract C: RedactionResult
                   │
                   ▼
  Stage 7: Release Gate Evaluation & Authorization
     - Evaluate dual-key condition: (verification_status == "PASS") AND (release_allowed == True)
     - If approved: transition to RELEASED, authorize client artifact download
     - If failed: transition to BLOCKED, deny download access, record findings
     - If exception: transition to FAILED, deny download access, sanitize error
                   │
                   ▼
  Telemetry, Reporting & Presentation
     - Log allowlist-projected events to thread-safe AuditTrail
     - Generate Contract D ProcessingReport
     - Present live results, metrics, and gated download buttons in app.py
```

---

## 4. Canonical Inter-Module Data Contracts

### Contract A: `ExtractedDocument` (Ingestion -> Downstream)
* **Location:** `src/pii_guard/ingestion/schemas.py`
* **Producer:** `src/pii_guard/ingestion/extractor.py:extract_document()`
* **Fields:**
  * `document_id: str` — Unique UUID identifier
  * `source_type: Literal["pdf", "docx", "pptx", "txt"]`
  * `text: str` — Immutable normalized Unicode source of truth
  * `pages: list[PageInfo]` — Per-page character offset intervals `[start, end)`
  * `warnings: list[WarningInfo]` — Non-fatal diagnostic warnings
  * `extraction_status: Literal["success", "partial", "failed"]`

### Contract B: `DetectionResult` (Detection -> Redaction)
* **Location:** `src/pii_guard/detection/schemas.py` & `src/pii_guard/orchestration/models.py`
* **Producer:** `src/pii_guard/detection/detector.py:detect_pii()`
* **Fields:**
  * `document_id: str` — Bound to `ExtractedDocument.document_id`
  * `entities: list[DetectedEntity]` — Each with `type: str`, `start: int`, `end: int`, `confidence: float`
  * `warnings: list[DetectionWarning | str]` — Sanitized diagnostic warnings

### Contract C: `RedactionResult` (Redaction -> Orchestration)
* **Location:** `src/pii_guard/redaction/schemas.py` & `src/pii_guard/orchestration/models.py`
* **Producer:** `src/pii_guard/redaction/service.py:redact_and_validate()`
* **Fields:**
  * `document_id: str` — Document UUID
  * `artifact_ref: Optional[str]` — Opaque sandbox artifact token (`art-<uuid>`)
  * `redactions_applied: int` — Total count of masked PII entities
  * `verification_status: Literal["PASS", "FAIL", "INCOMPLETE"]`
  * `release_allowed: bool` — Gate release permission flag
  * `findings: list[RedactionFinding | FindingInfo]` — Sanitized findings

### Contract D: `ProcessingReport` (Orchestration -> Audit / Client)
* **Location:** `src/pii_guard/orchestration/models.py`
* **Producer:** `src/pii_guard/reporting/report_generator.py:generate_report()`
* **Fields:**
  * `document_id: str`
  * `workflow_status: Literal["success", "blocked", "failed", "incomplete"]`
  * `category_counts: dict[str, int]` — PII counts aggregated by taxonomy label
  * `verification_status: Literal["PASS", "FAIL", "INCOMPLETE"]`
  * `release_allowed: bool`
  * `created_at: datetime`
  * `execution_time_sec: float`
  * `stages_completed: list[str]`
  * `safe_warnings: list[str]`

---

## 5. Identified Integration Defects & Risks (Pre-Fix Baseline)

1. **Unresolved Merge Conflict Markers on Remote Branch:**
   During earlier branch merges, merge conflict markers (`<<<<<<< HEAD`, `=======`, `>>>>>>>`) were committed into multiple source and test files (`src/pii_guard/detection/__init__.py`, `classifier.py`, `pattern_detector.py`, `validators.py`, `src/pii_guard/redaction/__init__.py`, `redactor.py`, `service.py`, `tests/test_detection.py`, `README.md`, `docs/detection.md`, `docs/security.md`, `evaluation/build_ground_truth.py`, `ground_truth.jsonl`).
   * **Impact:** Causes syntax errors during import and test collection; causes pipeline Stage 4 (DETECTED) to abort with `ERR_PIPELINE_FAILED`.

2. **`PIIDetector` Regression in `detector.py`:**
   In `src/pii_guard/detection/detector.py`, `self.ner_backend = ner_backend` was added to `__init__(self, confidence_threshold: float = 0.5)` without `ner_backend` being accepted in the argument list, causing a runtime `NameError`.
   Furthermore, Member 2's comprehensive detection implementation was replaced with a simplified regex snippet.
   * **Impact:** Broken instantiation of `PIIDetector` and loss of Member 2's validated multi-format detection and overlap resolution.

3. **Redaction Facade Parameter Alignment in `redactor.py` and `service.py`:**
   Member 3 implemented `service.py:redact_and_validate` accepting `(document, detection_result, *, artifact_ref, artifact_text_reader, minimum_structure_score)`.
   Member 5's pipeline coordinator in `pipeline.py` calls `redact_and_validate(extracted_doc, detection_res, artifact_manager=art_mgr, simulate_verification_failure=sim_fail)`.
   * **Impact:** Mismatch in keyword arguments if not bridged cleanly in `service.py` and `redactor.py`.

4. **External Dependency Handling for Scanned PDF OCR:**
   On Windows hosts without an external Tesseract executable installed on `PATH`, OCR tests in `tests/test_ingestion.py` fail with `failed` extraction status.
   * **Impact:** Non-OCR digital documents (PDF, Word, PPTX, TXT) process cleanly (17/20 pass), but scanned PDF tests require graceful environment detection or clear documentation of host prerequisites.

---

## 6. Architecture Preservation Assurance

The existing modular architecture, pipeline lifecycle, data contracts, and security boundaries are 100% preserved. No frameworks or architectural layers will be introduced. Every fix will adhere strictly to minimal-change root-cause correction.
