# PII Guard: Live Implementation Demonstration Runbook

### Cadence Financial Group — Cyber Strategy & Automated AI Redaction Release Gate

This document serves as the official presenter and evaluator guide for demonstrating the live execution of the PII Guard pipeline. It details the setup commands, synthetic demonstration scenarios, stage-by-stage runtime observations, fail-closed release gate validation, error handling, and troubleshooting procedures.

---

## 1. Quickstart & Launch Instructions

### 1.1 Environment Setup (Windows PowerShell)

```powershell
# Navigate to repository root
cd D:\Dev_Projects\Optive_Case_study

# Activate Python 3.12 / 3.13 virtual environment
.\.venv\Scripts\activate

# Verify dependencies are satisfied
pip install -r requirements.txt
pip install -r requirements-ingestion.txt
```

### 1.2 Launch the Modern React/TypeScript Web Application

```powershell
# Option A: Run Unified Production Application (FastAPI serves built React UI at http://localhost:8000)
python server.py

# Option B: Run with Vite Hot-Reloading Dev Server
# Terminal 1: Start Backend API Adapter (port 8000)
python -m uvicorn server:app --host 127.0.0.1 --port 8000

# Terminal 2: Start Vite React Frontend (port 5173)
cd frontend
npm run dev
# Open browser at http://localhost:5173 (proxies /api to port 8000)
```

---

## 2. Certified Demonstration Scenarios

The system includes pre-configured, deterministic synthetic scenarios located in `demo_samples/fixtures/`. All sensitive tokens are synthetic demo values created under `--seed 42` and validated against ground-truth manifest schemas.

| Scenario ID | Scenario Name | Fixture File | Input Characteristics | Expected Outcome |
| :---: | :--- | :--- | :--- | :--- |
| **SC-01** | **Single Category PII** | `01_synthetic_email.txt` | Customer banking advisory email with 1 Email entity | `PASS` / `RELEASED`<br>1 `<EMAIL_ADDRESS_1>` masked |
| **SC-02** | **Multi-Category PII** | `03_mixed_pii.txt` | Loan transfer document with SSN, Phone, Email, Credit Card, IP address | `PASS` / `RELEASED`<br>Multi-category masked right-to-left |
| **SC-03** | **Clean / Benign Document** | `04_clean_no_pii.txt` | Public market economic update containing 0 PII entities | `PASS` / `RELEASED`<br>0 entities detected, 0 redactions |
| **SC-04** | **Repeated Entities** | `05_repeated_entities.txt` | Multiple occurrences of the same client SSN and name | `PASS` / `RELEASED`<br>All occurrences masked uniformly |
| **SC-05** | **Complex Layout DOCX** | `06_multi_category.docx` | Native Microsoft Word document with tables and paragraphs | `PASS` / `RELEASED`<br>Layout & structure retained |
| **SC-06** | **International & Unicode** | `07_unicode_international.txt` | Indian PAN cards, international phones, Unicode accents | `PASS` / `RELEASED`<br>NFC-normalized unicode preserved |
| **SC-07** | **Security: Empty Payload** | `08_empty_document.txt` | 0-byte file payload | **Validation Rejected**<br>Fail-closed pre-ingestion check |
| **SC-08** | **Security: Unsupported File** | `10_malformed_binary.xyz` | Arbitrary unsupported binary payload | **Validation Rejected**<br>Extension sniffing security guard |
| **SC-09** | **Security: Residual Leakage** | `03_mixed_pii.txt` *(simulated)* | Verification failure injection toggle enabled | `FAIL` / `BLOCKED`<br>Download button disabled |

---

## 3. Presenter Walkthrough: Step-by-Step

### Scenario 1: Standard Authorized Processing Walkthrough (SC-02: Mixed PII)

1. **Select Input Mode:**
   - In the sidebar, select **"🧪 Pre-built Demo Scenarios"**.
   - Select **"2. Multi-Category PII (Wire Transfer & Loan)"**.
   - Ensure the "Simulate Verification Leakage" checkbox is **unchecked**.
2. **Execute Pipeline:**
   - Click the **"🚀 Execute Protection Pipeline"** button.
   - The progress indicator will track real backend stage progression.
3. **Inspect the Outcome:**
   - **Banner Displayed:**
     ```
     ✅ RELEASE AUTHORIZED
     Verification Status: PASS — All detected PII was safely masked. Post-redaction re-scan detected 0 residual leaks.
     ```
   - **Operational Metrics Bar:**
     - Displays Document UUID, Format (`TXT`), Pages (`1`), Entities Detected (`5+`), Redactions Masked (`5+`).
4. **Inspect Tabs:**
   - **⏱️ Stage Execution Timeline:**
     - View the real-time stage progression table recorded by `PipelineStateManager`:
       `RECEIVED` $\rightarrow$ `VALIDATED` $\rightarrow$ `EXTRACTED` $\rightarrow$ `DETECTED` $\rightarrow$ `REDACTED` $\rightarrow$ `VERIFIED` $\rightarrow$ `RELEASED`.
     - Review the exact UTC timestamps and sub-second stage durations.
   - **📊 Detected Categories:**
     - Examine the breakdown of detected PII types (`US_SSN`, `EMAIL_ADDRESS`, `PHONE_NUMBER`, `CREDIT_CARD`, `IPV4_ADDRESS`).
   - **👁️ Redacted Preview:**
     - View the masked text: sensitive entities are replaced with contextual tokens (`<US_SSN_1>`, `<EMAIL_ADDRESS_1>`).
   - **📜 Sanitized Audit Trail:**
     - Inspect the immutable, metadata-only event ledger: note that document IDs, stage transitions, and categories are logged, but **zero raw text or PII values** are retained.
   - **📑 Formal Report:**
     - Review the Contract D executive summary and compliance metadata.
5. **Download Approved Artifact:**
   - Click **"📥 Download Approved Redacted Artifact"** to download the sanitized document.
   - Click **"📥 Download Sanitized Audit Report (JSON)"** to download the Contract D compliance audit record.

---

### Scenario 2: Fail-Closed Security Walkthrough (SC-09: Residual Leakage Simulation)

1. **Enable Failure Simulation:**
   - In the sidebar, check the box: **"Simulate Verification Leakage (Test Blocked Gate)"**.
   - Select scenario **"2. Multi-Category PII (Wire Transfer & Loan)"**.
2. **Execute Pipeline:**
   - Click **"🚀 Execute Protection Pipeline"**.
3. **Inspect the Security Outcome:**
   - **Prominent Red Warning Banner Displayed:**
     ```
     🛑 RELEASE BLOCKED (DOWNLOAD WITHHELD)
     Verification Status: FAIL — Independent verification detected residual sensitive tokens or policy exception. Client download is strictly disabled.
     ```
   - **Release Gate Invariant Proven:**
     - The "Redacted Preview" tab is **disabled** with a security warning.
     - The download action displays: **"🔒 Download Blocked (Verification Incomplete or Failed)"** in a disabled, non-clickable state.
     - State machine transitions to `BLOCKED`.
     - Audit trail logs `VERIFICATION_FAILED` event.
4. **Takeaway for Cadence Financial Group:**
   - Proves mathematically that even if an internal redaction fault occurs, the secondary independent re-scan intercepts the leakage and blocks client artifact egress.

---

### Scenario 3: Pre-Ingestion Security Boundaries (SC-07 & SC-08)

1. **Select SC-07 (Empty Document):**
   - In Demo Scenarios, select **"7. Security Boundary: Empty Document (0 Bytes)"**.
   - Notice the immediate error:
     ```
     ❌ Input Validation Failed (Security Boundary): Uploaded file is 0 bytes (empty).
     ```
   - Execution is halted before touching disk or downstream parsers.
2. **Select SC-08 (Unsupported Binary):**
   - Select **"8. Security Boundary: Unsupported Binary (.xyz)"**.
   - Notice the extension sniffing rejection:
     ```
     ❌ Input Validation Failed (Security Boundary): Unsupported file extension '.xyz'. Supported: .pdf, .docx, .pptx, .txt, .text
     ```

---

## 4. Backend Call Chain & Module Ownership Reference

| Step | Lifecycle Stage | Backend Module & Owner | Interface Contract | Key Invariants Enforced |
| :---: | :--- | :--- | :---: | :--- |
| **1** | `RECEIVED` / `VALIDATED` | `pii_guard.ingestion.validator`<br>*(Member 1: Ayush Sinha)* | Pre-ingestion | Magic byte sniffing, max file size (50MB), zip bomb defense ($\le 100:1$). |
| **2** | `EXTRACTED` | `pii_guard.ingestion.extractor`<br>*(Member 1: Ayush Sinha)* | **Contract A**<br>`ExtractedDocument` | Layout preservation, single-pass Unicode NFC normalizer, deterministic character offsets. |
| **3** | `DETECTED` | `pii_guard.detection.detector`<br>*(Member 2: Avishi Sharma)* | **Contract B**<br>`DetectionResult` | Deterministic regex matchers, Luhn algorithm, overlap resolution, page-boundary containment. |
| **4** | `REDACTED` | `pii_guard.redaction.redactor`<br>*(Member 3: Yash Jhinkwan)* | **Contract C**<br>`RedactionResult` | Contextual token replacement applied right-to-left to preserve source offsets. |
| **5** | `VERIFIED` | `pii_guard.redaction.verifier`<br>*(Member 3: Yash Jhinkwan)* | Verification Gate | Reopens saved artifact and conducts independent secondary re-scan for residual PII tokens. |
| **6** | `RELEASED` / `BLOCKED` | `pii_guard.orchestration.pipeline`<br>*(Member 5: Tirth Bora)* | Finite State Machine | Dual-key release barrier: release allowed strictly when `verification_status == "PASS"`. |
| **7** | `AUDITED` / `REPORTED` | `pii_guard.reporting.audit`<br>*(Member 5: Tirth Bora & M4: Anshika)* | **Contract D**<br>`ProcessingReport` | Thread-safe, allowlist-only audit log; zero raw PII retention in logs or exports. |

---

## 5. Troubleshooting & Environmental Notes

### 5.1 OCR Binary Availability (Tesseract)
- On hosts with a standard Tesseract OCR executable installed on the system PATH, scanned image-only PDFs run through the adaptive OCR engine automatically.
- On hosts without Tesseract on PATH, digital PDFs, DOCX, PPTX, and TXT documents process with full 100% throughput and fidelity. Scanned PDF extraction tests are gracefully skipped by test automation with informative notices.
- To specify a custom Tesseract path on Windows, set the environment variable:
  ```powershell
  $env:TESSERACT_CMD = "C:\Program Files\Tesseract-OCR\tesseract.exe"
  ```

### 5.2 Streamlit Port Conflicts
- If port 8501 is occupied, launch on an alternate port:
  ```powershell
  streamlit run app.py --server.port 8502
  ```

### 5.3 Temporary File Handling
- All uploaded documents are processed in secure, isolated temporary files and automatically unlinked upon pipeline completion, even in exception states.
