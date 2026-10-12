# PII Guard: Enterprise Text Analysis & PII Protection Pipeline
### Cadence Financial Group — Cyber Strategy & AI Governance Case Study

A modular, privacy-first document processing pipeline built for **Cadence Financial Group** to enforce strict data protection controls before business artifacts reach downstream AI and Large Language Model (LLM) agents.

---

## 1. Team Roster & Revised Division of Work

Based on the updated architectural specification (`PII_Case_Study_Named_Team_Detailed_Architecture_REVISED.pdf`), the team division is partitioned into strictly bounded technical and presentation tracks:

| Member / Owner | Role | Primary Deliverables & Owned Paths | Added / Bounded Work | Must NOT Own |
| :--- | :--- | :--- | :--- | :--- |
| **Member 1: Ayush Sinha** *(You)* | **Ingestion, Extraction & OCR** | `src/pii_guard/ingestion/`<br>`tests/test_ingestion.py`<br>`docs/ingestion.md` | Deterministic synthetic fixtures, extraction completeness & $\ge 80\%$ structure retention scoring. | Detection internals, redaction policies, UI. |
| **Member 2: Avishi Sharma** | **PII Detection & Classification** | `src/pii_guard/detection/`<br>`tests/test_detection.py`<br>`evaluation/` | Synthetic ground-truth annotations, precision, recall, F1 metrics, false-negative analysis. | Ingestion parsers, redaction policies, UI. |
| **Member 3: Yash** | **Redaction, Verification & Release Gate** | `src/pii_guard/redaction/`<br>`tests/test_redaction.py`<br>`docs/security.md` | Leakage tests, saved-artifact verification, non-sensitive structure preservation. | Detection internals, UI orchestration. |
| **Member 4: Nancy** | **PowerPoint Presentation & Demo Fixtures** | `demo_tools/`<br>`demo_samples/`<br>`tests/test_demo_fixtures.py`<br>`Presentation (.pptx)` | 75% slide deck narrative & rehearsal; 25% lightweight synthetic demo-fixture generator & manifest. | Core detection/redaction algorithms, orchestration. |
| **Member 5: Tirth** | **Orchestration, UI, Audit & Integration** | `src/pii_guard/orchestration/`<br>`src/pii_guard/reporting/`<br>`app.py`<br>`tests/test_integration.py` | Cross-module state machine, release gate enforcement, metadata-only audit reporting. | Internal extraction or detection algorithms. |

> **Roster Note:** If Anshika is also participating, the team should confirm whether she contributes alongside Member 5 or takes a specialized sub-track.

---

## 2. Key Capabilities

- **Multi-Format Extraction:** Preserves visual reading order and layout across digital PDFs, scanned documents, Word documents, PowerPoint presentations, and plain text.
- **Adaptive OCR Engine:** High-speed 200 DPI fast-path rasterization with 300 DPI fallback, OpenCV deskewing, and adaptive Otsu binarization for degraded scans.
- **Fail-Closed Security Layer:** Magic byte sniffing (rejects renamed binaries), zip-bomb defense (ratio $\le 100:1$), encrypted PDF blocking, and zero unhandled exceptions.
- **Deterministic Downstream Offsets:** Single-pass Unicode NFC normalizer ensuring `text` is the immutable source of truth for downstream detection spans.
- **Accurate PII Detection & Redaction:** Entity identification with contextual token masking (`<PERSON_1>`, `<EMP_ID_1>`).
- **Release Gate & Audit Logging:** Hard barrier blocking downloads unless verification is strictly `PASS`.

---

## 3. Project Structure

```text
├── README.md                           # Project overview, team roster & architecture
├── requirements-ingestion.txt          # Pinned ingestion dependencies
├── requirements.txt                    # Team shared dependencies
├── pytest.ini                          # Test configuration
├── .gitignore                          # Git ignore rules (strictly excludes *.pdf)
│
├── src/
│   └── pii_guard/
│       ├── ingestion/                  # Member 1 (Ayush Sinha) - Ingestion & OCR
│       │   ├── adapters/               # Format adapters (PDF, DOCX, PPTX, TXT)
│       │   ├── config.py               # Timeouts, limits, and Tesseract path resolution
│       │   ├── extractor.py            # Central orchestration & offset calculator
│       │   ├── normalize.py            # Single-pass deterministic normalizer
│       │   ├── ocr.py                  # Tesseract & RapidOCR adaptive engines
│       │   ├── quality.py              # Extraction completeness & structure metrics
│       │   ├── router.py               # Format registry router
│       │   ├── schemas.py              # Pydantic v2 ExtractedDocument contract
│       │   └── validator.py            # Magic byte, zip-bomb, and security checks
│       ├── detection/                  # Member 2 (Avishi Sharma) - PII Detection
│       ├── redaction/                  # Member 3 (Yash) - Redaction & Release Gate
│       ├── orchestration/              # Member 5 (Tirth) - Pipeline state machine
│       └── reporting/                  # Member 5 (Tirth) - Audit & report generation
│
├── benchmarks/
│   └── bench_ingestion.py              # Ingestion throughput and latency benchmark
├── docs/
│   └── ingestion.md                    # Ingestion module handbook & Nancy handoff
├── tests/
│   ├── test_ingestion.py               # 19 automated tests for Member 1
│   └── fixtures/ingestion/             # Deterministic synthetic test fixtures
└── demo_tools/                         # Member 4 (Nancy) - Lightweight demo generator
```

---

## 4. Quickstart

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

### 2. Install Ingestion Dependencies
```bash
pip install -r requirements-ingestion.txt
```

### 3. Run Ingestion Tests & Benchmarks
```bash
# Run test suite (all 19 tests pass)
pytest -q tests/test_ingestion.py

# Run performance benchmark
python benchmarks/bench_ingestion.py
```

### 4. CLI Usage
```bash
python -m src.pii_guard.ingestion tests/fixtures/ingestion/sample.docx --json
```
