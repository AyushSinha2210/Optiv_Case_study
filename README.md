# PII Guard: Enterprise Text Analysis & PII Protection Pipeline
### Cadence Financial Group — Cyber Strategy & AI Governance Case Study

A modular, privacy-first document processing pipeline built for **Cadence Financial Group** to enforce strict data protection controls before business artifacts reach downstream AI and Large Language Model (LLM) agents.

---

## 1. Team Roster & Revised Division of Work

Based on the updated architectural specification (`PII_Case_Study_Named_Team_Detailed_Architecture_REVISED.pdf`), the team division is partitioned into strictly bounded technical and presentation tracks:

| Member / Owner | Role | Primary Deliverables & Owned Paths | Added / Bounded Work | Implementation Status |
| :--- | :--- | :--- | :--- | :---: |
| **Member 1: Ayush Sinha** *(You)* | **Ingestion, Extraction & OCR** | `src/pii_guard/ingestion/`<br>`tests/test_ingestion.py`<br>`docs/ingestion.md` | Layout-preserving parsers (PDF, DOCX, PPTX, TXT), adaptive OCR, magic byte sniffing, zip-bomb defense, $\ge 80\%$ structure retention scoring. | **COMPLETED** |
| **Member 2: Avishi Sharma** | **PII Detection & Classification** | `src/pii_guard/detection/`<br>`tests/test_detection.py`<br>`evaluation/` | Entity identification, span classification, regex & pattern rules, detection confidence scores, ground-truth annotations. | **COMPLETED / INTEGRATED** |
| **Member 3: Yash Jhinkwan** | **Redaction, Verification & Release Gate** | `src/pii_guard/redaction/`<br>`tests/test_redaction.py`<br>`docs/security.md` | Contextual token replacement (`[REDACTED_...]`), secondary re-scan verification, saved-artifact checks, structure preservation. | **COMPLETED / INTEGRATED** |
| **Member 4: Anshika** | **Demo Fixtures, Manifest & Presentation** | `demo_tools/`<br>`demo_samples/`<br>`src/pii_guard/reporting/metrics.py`<br>`tests/evaluation/`<br>`Presentation (.pptx)` | Deterministic synthetic PII generator (`--seed`), ground-truth manifest, bipartite matching evaluation metrics (Precision, Recall, F1, FNR, IoU), PowerPoint slide deck narrative & rehearsal. | **COMPLETED** |
| **Member 5: Tirth Bora** | **Orchestration, UI, Audit & Integration** | `src/pii_guard/orchestration/`<br>`src/pii_guard/reporting/`<br>`app.py`<br>`tests/unit/`, `tests/integration/`, `tests/security/` | Cross-module finite state machine, dual-key release gate barrier, tokenized artifact sandbox, metadata-only audit ledger, Streamlit UI, end-to-end integration tests. | **COMPLETED** |

---

## 2. Key Capabilities

- **Multi-Format Extraction:** Preserves visual reading order and layout across digital PDFs, scanned documents, Word documents, PowerPoint presentations, and plain text.
- **Adaptive OCR Engine:** High-speed 200 DPI fast-path rasterization with 300 DPI fallback, OpenCV deskewing, and adaptive Otsu binarization for degraded scans.
- **Fail-Closed Security Layer:** Magic byte sniffing (rejects renamed binaries), zip-bomb defense (ratio $\le 100:1$), encrypted PDF blocking, and zero unhandled exceptions.
- **Deterministic Downstream Offsets:** Single-pass Unicode NFC normalizer ensuring `text` is the immutable source of truth for downstream detection spans.
- **Accurate PII Detection & Redaction:** Entity identification with contextual token masking (`[REDACTED_PERSON]`, `[REDACTED_EMAIL]`, `[REDACTED_ID]`).
- **Dual-Key Release Gate:** Hard barrier blocking downloads unless verification is strictly `PASS` and `release_allowed=true`.
- **Zero-Leakage Audit Trail:** Metadata-only audit ledger ensuring raw PII is never recorded in logs or exports.
- **Interactive Streamlit UI:** Complete web application with side-by-side inspection, stage telemetry, and gated artifact downloads.

---

## 3. System Architecture & Trust Boundaries

The system is partitioned into three independent operational planes to ensure privacy, performance, and clear developer boundaries:

```mermaid
flowchart TD
    subgraph StoragePlane["Storage & Quarantine Plane"]
        S1[(Quarantine Store<br/>Short-lived original files)]
        S2[(Sanitized Output Store<br/>Only if PASS & release_allowed=true)]
        S3[(Audit Store<br/>Metadata-only, no raw text)]
    end

    subgraph RuntimePlane["Runtime Data Plane (Live Pipeline)"]
        A[Client Upload / API] --> B[1. Validation & Sniffing<br/>Member 1: Ayush]
        B --> C[2. Layout-Preserving Extraction & OCR<br/>Member 1: Ayush]
        C --> D[3. PII Detection & Classification<br/>Member 2: Avishi]
        D --> E[4. Redaction & Verification Gate<br/>Member 3: Yash]
        E --> F[5. State Machine & Audit Report<br/>Member 5: Tirth]
        F --> G{Release Gate<br/>PASS?}
        G -->|Yes: release_allowed=true| H[Download Approved]
        G -->|No: FAIL / INCOMPLETE| I[BLOCKED: Download Disabled]
    end

    subgraph QualityPlane["Independent Quality Plane (Offline / CI)"]
        Q1[Member 1: Extraction Quality & >=80% Structure Benchmarks]
        Q2[Member 2: Ground Truth & Precision / Recall / F1 Evaluation]
        Q3[Member 3: Leakage Tests & Saved-Artifact Checks]
        Q4[Member 4: Synthetic Demo Pack & PPT Slide Deck]
        Q5[Member 5: Cross-Module Integration Tests]
    end

    A -.-> S1
    E -.-> S2
    F -.-> S3
```

### Pipeline Lifecycle States
`RECEIVED` $\rightarrow$ `VALIDATED` $\rightarrow$ `EXTRACTED` $\rightarrow$ `DETECTED` $\rightarrow$ `REDACTED` $\rightarrow$ `VERIFIED` $\rightarrow$ `RELEASED`
- Any technical fault transitions to `FAILED`.
- Any unverified or leaking redaction transitions to `BLOCKED`.
- Any missing required verification transitions to `INCOMPLETE`.
- All states except verified `PASS` prevent client download.

---

## 4. Shared Interface Contracts

To allow all five team members to develop and test concurrently without blocking dependencies, communication between modules is governed by four strict, immutable data contracts (see [`docs/interfaces.md`](file:///c:/Users/AYUSH%20SINHA/Optiv/docs/interfaces.md) for full JSON schemas):

| Contract | Schema Name | Producer | Consumer | Key Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Contract A** | `ExtractedDocument` | **Member 1 (Ayush)** | **Member 2 (Avishi)** | Normalized single-source-of-truth text, exact character offsets, and per-page OCR confidence. |
| **Contract B** | `DetectionResult` | **Member 2 (Avishi)** | **Member 3 (Yash)** | Classified entity spans (`type`, `start`, `end`, `confidence`) mapped into `ExtractedDocument.text`. |
| **Contract C** | `RedactionResult` | **Member 3 (Yash)** | **Member 5 (Tirth)** | Redacted output, verification outcome (`PASS`/`FAIL`/`INCOMPLETE`), and `release_allowed` boolean flag. |
| **Contract D** | `ProcessingReport` | **Member 5 (Tirth)** | **Auditor / Client** | Metadata-only audit ledger (entity counts by category, timestamps, versions); strictly no raw PII. |

---

## 5. Project Structure

```text
├── README.md                           # Project overview, team roster & architecture
├── requirements-ingestion.txt          # Pinned ingestion dependencies
├── requirements.txt                    # Team shared dependencies
├── pytest.ini                          # Test configuration
├── .gitignore                          # Git ignore rules (strictly excludes *.pdf)
├── app.py                              # Member 5 - Interactive Streamlit application
│
├── src/pii_guard/
│   ├── ingestion/                      # Member 1 (Ayush) - Ingestion & OCR
│   │   ├── adapters/                   # PDF, DOCX, PPTX, and TXT format adapters
│   │   ├── config.py                   # Ingestion configuration and env overrides
│   │   ├── extractor.py                # Public Contract A API (extract_document)
│   │   ├── normalize.py                # Single-source-of-truth Unicode NFC normalizer
│   │   ├── ocr.py                      # Selective adaptive OCR engine
│   │   ├── quality.py                  # Structure score & completeness validator
│   │   └── validator.py                # Magic byte sniffing & zip bomb defense
│   │
│   ├── detection/                      # Member 2 (Avishi) - Detection & Classification
│   │   ├── classifier.py               # Precedence and overlap resolution
│   │   ├── detector.py                 # Public Contract B API (detect_pii, PIIDetector)
│   │   ├── ner_detector.py             # Optional SpaCy NER adapter
│   │   ├── pattern_detector.py         # Pattern rules (SSN, PAN, Email, Phone, IP, Luhn)
│   │   ├── schemas.py                  # Contract B schemas & exception models
│   │   └── validators.py               # Input validation for Contract B
│   │
│   ├── redaction/                      # Member 3 (Yash) - Redaction & Verification
│   │   ├── gate.py                     # Release evaluation logic
│   │   ├── policy.py                   # Token replacement policies
│   │   ├── redactor.py                 # Offset-safe masking engine & Redactor wrapper
│   │   ├── schemas.py                  # Contract C schemas (RedactionResult)
│   │   ├── service.py                  # redact_and_validate entry point
│   │   └── verifier.py                 # Post-redaction residual leakage verifier
│   │
│   ├── orchestration/                  # Member 5 (Tirth) - Pipeline & Security
│   │   ├── artifacts.py                # Opaque tokenized artifact sandbox
│   │   ├── errors.py                   # Sanitized error hierarchy & regex guards
│   │   ├── models.py                   # Orchestration Pydantic v2 data models
│   │   ├── pipeline.py                 # End-to-end coordinator (process_document)
│   │   └── state.py                    # Finite state machine (7 pipeline stages)
│   │
│   └── reporting/                      # Member 5 (Tirth) - Audit & Evaluation
│       ├── audit.py                    # Thread-safe metadata-only audit ledger
│       ├── export.py                   # Allowlist JSON and CSV exporters
│       ├── metrics.py                  # Member 4 - Bipartite matching detection metrics
│       └── report_generator.py         # Contract D JSON report & executive summary
│
├── demo_tools/                         # Member 4 (Anshika) - Synthetic Data Generator
│   └── generate_synthetic_samples.py   # Seeded deterministic generator (10 scenarios)
├── demo_samples/                       # Generated synthetic fixtures & manifest
│   ├── manifest.json                   # Ground-truth annotations & metadata
│   └── *.txt / *.xyz                   # Test fixtures (emails, loans, wires, attacks)
│
├── docs/                               # Engineering Documentation
│   ├── architecture.md                 # System architecture, operational planes & state machine
│   ├── security.md                     # Security controls, threat model & invariants
│   ├── evaluation.md                   # Detection evaluation metrics & matching rules
│   ├── demo_script.md                  # Step-by-step presentation walkthrough
│   ├── ingestion.md                    # Ingestion module handbook & Anshika handoff
│   ├── detection.md                    # Detection module handbook & synthetic evaluation
│   ├── interfaces.md                   # Full JSON schemas for Contracts A, B, C, D
│   ├── member5_member4_commit_log.md   # Chronological commit log & audit record
│   └── member5_member4_implementation_plan.md # Checklist of completed deliverables
│
├── benchmarks/
│   └── bench_ingestion.py              # Ingestion throughput and latency benchmark
│
├── evaluation/                         # Member 2 Evaluation & Ground Truth
│   ├── build_ground_truth.py           # Evaluation corpus builder
│   └── ground_truth.jsonl              # 28 annotated evaluation documents
│
└── tests/                              # Comprehensive Automated Test Suite
    ├── test_cli.py                     # CLI output mode tests
    ├── test_config.py                  # Configuration and env override tests
    ├── test_detection.py               # 57 automated tests for Member 2
    ├── test_ingestion.py               # Ingestion automated tests for Member 1
    ├── test_redaction.py               # Redaction and verification tests for Member 3
    ├── unit/                           # Unit tests for state, errors, audit, reporting, UI
    ├── evaluation/                     # Detection evaluation & bipartite metric tests
    ├── integration/                    # End-to-end pipeline coordination tests
    ├── security/                       # Fail-closed release gate, leakage & traversal tests
    └── fixtures/                       # Test fixture files
```

---

## 6. Extraction Quality & Performance Benchmarks (Member 1)

$$\text{Structure Score} = 0.25 \times \text{Boundaries} + 0.25 \times \text{Headings} + 0.20 \times \text{Paragraphs} + 0.20 \times \text{Tables} + 0.10 \times \text{Reading Order}$$

| Format / Payload | Sample Size | Completeness (RapidFuzz) | Structure Retention Score | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Word Document (DOCX)** | 1 document | **100.0%** | **100.0%** | **PASS** ($\ge 80\%$) |
| **Digital PDF** | 2 pages | **100.0%** | **100.0%** | **PASS** ($\ge 80\%$) |
| **PowerPoint (PPTX)** | 2 slides | **100.0%** | **100.0%** | **PASS** ($\ge 80\%$) |
| **Composite Average** | **5 artifacts** | **100.0%** | **100.0%** | **PASS** ($\ge 80\%$) |

Throughput measured up to **981.6 pages/sec** (Digital PDF) and **4,684 pages/sec** (TXT stream).

---

## 7. Quickstart

### 1. Setup Virtual Environment
```bash
# Clone the repository
git clone https://github.com/AyushSinha2210/Optive_Case_study.git
cd Optive_Case_study

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-ingestion.txt
```

### 3. Run Automated Tests
```bash
# Run unit, integration, and security tests
pytest tests/unit tests/integration tests/security -v

# Run individual module suites
pytest tests/test_detection.py tests/test_redaction.py -v
```

### 4. Interactive Streamlit UI
```bash
streamlit run app.py
```

### 5. CLI Usage
```bash
python -m src.pii_guard.ingestion tests/fixtures/ingestion/sample.docx --json
```

---

## 8. Definition of Done (DoD) & Acceptance Criteria

### Member 1 Deliverables (Ayush Sinha)
- **Public API Contract A:** `extract_document(file_path)` returns Pydantic v2 `ExtractedDocument` matching schema.
- **Multi-Format Adapters:** `PDFAdapter`, `DOCXAdapter`, `PPTXAdapter`, and `TXTAdapter` implemented in `adapters/`.
- **Layout & Structure Preservation:** Interleaved paragraphs and tables in DOCX, reading order in PDF, slide hierarchy in PPTX.
- **Selective Adaptive OCR:** Fast-path rasterization with selective Tesseract triggers at 200 DPI, 300 DPI fallback with OpenCV deskew.
- **Malicious & Sanity Defenses:** Sniffs real magic bytes; rejects renamed `.exe`, zip bombs ($\le 100:1$), and encrypted PDFs.
- **Structure Retention Score $\ge 80\%$:** Quantitative weighted score achieved **100.0%** across DOCX, PDF, and PPTX fixtures.

### Member 2 Deliverables (Avishi Sharma)
- **Public API Contract B:** `detect_pii(document)` returning validated `DetectionResult` with `PII_TYPES`.
- **Deterministic Pattern Detectors:** Regex rules with Luhn algorithm validation, US SSN, IN PAN, Email, Phone, IP address.
- **Overlap Resolution:** Strict precedence ordering, span length, confidence, and start offset.
- **Fail-Closed Guarantees:** Rejects failed extractions; drops spans crossing page boundaries (`\f`).
- **Ground Truth Corpus:** 28 synthetic annotated documents with precision/recall/F1 evaluation tools.

### Member 3 Deliverables (Yash Jhinkwan)
- **Public API Contract C:** `redact_and_validate()` returning `RedactionResult` with strict `release_allowed` boolean.
- **Contextual Masking:** Offset-safe replacement applied right-to-left.
- **Saved-Artifact Re-scan:** Reopens stored artifact with format-specific reader before granting `PASS`.
- **Structure Score Enforcement:** Validates line boundaries and heading preservation post-redaction.

### Member 4 Deliverables (Anshika)
- **Deterministic Synthetic Fixture Generator:** `demo_tools/generate_synthetic_samples.py` producing 10 realistic scenarios.
- **Ground Truth Manifest:** `demo_samples/manifest.json` indexing spans, entity categories, and expected outcomes without raw PII.
- **Bipartite Matching Evaluation Engine:** `evaluate_predictions()` with exact, overlap, and IoU $\ge 0.50$ matching criteria.
- **Mathematical Metrics:** Computes TP, FP, FN, Precision, Recall, F1, and FNR with zero-denominator safety rules.
- **Presentation Deck:** PowerPoint presentation deck covering case study narrative and live demo scripts.

### Member 5 Deliverables (Tirth Bora)
- **Pipeline Finite State Machine:** `PipelineStateManager` enforcing monotonic transitions across 7 stages.
- **Dual-Key Fail-Closed Release Gate:** Access granted strictly when `verification_status == "PASS"` AND `release_allowed == True`.
- **Opaque Artifact Sandbox:** Cryptographic UUID tokens (`art-<uuid>`); rejects path traversal (`..`, `/`, `\`, `\x00`).
- **Sanitized Error Hierarchy:** `sanitize_error_message` strips filesystem paths, emails, phones, and SSNs from exceptions.
- **Thread-Safe Audit Trail:** `AuditTrail` recording allowlist-filtered events with atomic document ID relinking.
- **Contract D Structured Reporting:** Pydantic v2 `ProcessingReport` and executive summary generation with zero PII leakage.
- **Interactive Streamlit UI:** `app.py` with multi-format validation, progress indicators, side-by-side preview, and gated downloads.

---

## 9. Presentation Evidence Handoff for Anshika (Member 4)

Anshika can extract the following verified artifacts directly for the PowerPoint presentation deck:

- **Supported Formats Table:** PDF (Digital), PDF (Scanned OCR), Word (DOCX), PowerPoint (PPTX), Plain Text (TXT).
- **Quality Metric Benchmark:** Structure retention score = **100.0%** (exceeding the $\ge 80\%$ requirement) with sample size = 5 diverse artifacts.
- **Throughput Metric:** Digital PDF at **981.6 pages/sec**; DOCX at **117.0 pages/sec**; Tesseract OCR at **0.65 pages/sec**.
- **Known Limitation for Slides:** Degraded or heavily skewed scans (< 150 DPI) automatically trigger OCR low-confidence fallback and are marked `extraction_status="partial"` to prompt human review.

---

## 10. Environment Compatibility Notes

- **Python Version:** Python 3.12 and Python 3.13 are fully supported and tested.
- **OCR Dependencies:** `pytesseract` is configured as the default OCR engine. On systems without a local Tesseract binary installed on the OS PATH, pure text, Word, PowerPoint, and digital PDFs process natively, while image-only scanned PDFs require installing Tesseract or providing the binary path via `TESSERACT_CMD`.
