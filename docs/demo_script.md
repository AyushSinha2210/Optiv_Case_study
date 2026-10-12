# PII Guard: Demonstration Script & Walkthrough Guide
### Cadence Financial Group — Cyber Strategy & AI Governance Case Study
**Demonstration Leads:** Nancy (Member 4 Presentation) & Tirth (Member 5 System Demo)

---

## 1. Demonstration Objective

This script provides a structured, repeatable live-demonstration walkthrough of the **PII Guard** application for executive stakeholders, auditors, and technical evaluators at Cadence Financial Group. 

It highlights:
1. Multi-format ingestion and layout-preserving extraction.
2. High-precision PII detection and token-based redaction.
3. Dual-key fail-closed release authorization.
4. Opaque artifact sandboxing and zero-leakage audit compliance.
5. Deterministic synthetic test data and quantitative evaluation metrics.

---

## 2. Environment Preparation & Quickstart

### Step 1: Activate Virtual Environment
Open PowerShell / Terminal in the project root:
```powershell
# Navigate to project directory
cd D:\Dev_Projects\Optive_Case_study

# Activate the verified Python 3.13 virtual environment
.\.venv\Scripts\Activate.ps1
```

### Step 2: Generate Clean Synthetic Test Fixtures
Ensure deterministic synthetic samples are initialized:
```powershell
python -m demo_tools.generate_synthetic_samples --output-dir demo_samples --seed 42
```
*Expected Output:*
```text
[INFO] Generated 10 synthetic fixtures in 'demo_samples' using seed 42.
[INFO] Ground truth manifest saved to 'demo_samples/manifest.json'.
```

### Step 3: Launch the Streamlit Web Application
```powershell
streamlit run app.py
```
*Expected Output:*
Streamlit opens the local browser at `http://localhost:8501`.

---

## 3. Live Demonstration Walkthrough

### Scenario 1: Standard Customer Email (Happy Path Release)
**Objective:** Demonstrate automatic PII detection, redaction, independent verification, and approved artifact download.

1. **File to Upload:** `demo_samples/01_synthetic_email.txt`
2. **Action in UI:**
   - In the sidebar, leave the Detection Engine as Presidio + Fallback (`Threshold: 0.50`).
   - Drag and drop `01_synthetic_email.txt` into the upload widget.
   - Click the **"Run Privacy Pipeline"** button.
3. **What the Audience Sees:**
   - Animated progress bar stepping sequentially through:
     $$\text{RECEIVED} \to \text{VALIDATED} \to \text{EXTRACTED} \to \text{DETECTED} \to \text{REDACTED} \to \text{VERIFIED} \to \text{RELEASED}$$
   - **Green Banner:** `RELEASE AUTHORIZED: All PII successfully masked and verified.`
   - **Summary KPI Metrics:** Total Entities: 4 | Status: `PASS` | Release: `APPROVED` | Time: $< 150\text{ ms}$.
   - **Side-by-Side View:**
     - Left: Original text containing customer email (`jordan.smith@example.com`), phone, and SSN.
     - Right: Clean redacted text with replacements: `<EMAIL_ADDRESS_1>`, `<PHONE_NUMBER_1>`, `<US_SSN_1>`.
   - **Artifact Download:** The **"Download Redacted Document"** button is active and green.
4. **Presenter Narrative:**
   > *"Notice how the single-source-of-truth text coordinates ensure exact token replacement without distorting sentence syntax. Downstream AI agents can safely parse this message without learning the customer's real SSN or email."*

---

### Scenario 2: Multi-Entity Loan Application & Entity Breakdown
**Objective:** Demonstrate multi-category financial PII masking and structured compliance telemetry.

1. **File to Upload:** `demo_samples/02_synthetic_loan_application.txt`
2. **Action in UI:**
   - Upload `02_synthetic_loan_application.txt` and click **"Run Privacy Pipeline"**.
3. **What the Audience Sees:**
   - Detects 6 distinct entities across `US_SSN`, `US_BANK_NUMBER`, `PHONE_NUMBER`, `EMAIL_ADDRESS`, and `PERSON`.
   - Secondary verification completes with `PASS`.
   - Switch to the **"Compliance Report"** tab:
     - Shows the executive summary table and category breakdown.
     - Shows zero-leakage compliance confirmation.
4. **Presenter Narrative:**
   > *"In loan applications, banking credentials and tax IDs require zero-leakage guarantees. The report tab provides governance officers with aggregate counts by category while ensuring zero customer numbers enter the telemetry database."*

---

### Scenario 3: Fail-Closed Security Barrier (Release Blocked)
**Objective:** Prove that if verification fails or finds remaining unmasked PII, the system fails closed.

1. **Simulation in UI:**
   - In the sidebar, select **Verification Strictness:** *"Force Fail / Quarantine Test"*.
   - Upload `demo_samples/01_synthetic_email.txt` and click **"Run Privacy Pipeline"**.
2. **What the Audience Sees:**
   - The pipeline transitions to `BLOCKED`.
   - **Red Banner:** `RELEASE BLOCKED: Secondary verification failed or incomplete.`
   - The **"Download Redacted Document"** button is **disabled/grayed out**.
   - No artifact token is generated in the sandbox.
   - An audit record with event `RELEASE_DECISION` and status `BLOCKED` is permanently written.
3. **Presenter Narrative:**
   > *"Cadence operates on a zero-trust model. If secondary verification detects residual risk or fails to execute, download access is immediately revoked. The raw or unverified artifact is isolated in quarantine and never leaves the server."*

---

### Scenario 4: Malformed Input & Traversal Attack Defense
**Objective:** Demonstrate front-door defenses against malicious or invalid files.

1. **File to Upload:** `demo_samples/10_malformed_binary.xyz`
2. **What the Audience Sees:**
   - The upload validator rejects the file before processing:
     `[ERROR] Unsupported file extension '.xyz'. Supported formats: .pdf, .docx, .pptx, .txt.`
   - Zero stack traces or internal server paths are displayed.
3. **Presenter Narrative:**
   > *"Our front-door validation uses file type allowlists and magic byte sniffing to prevent renamed executables or corrupted payloads from reaching the extraction parsers."*

---

### Scenario 5: Audit Log Export & Zero-Leakage Verification
**Objective:** Prove that exported compliance logs are strictly free of raw PII.

1. **Action in UI:**
   - Switch to the **"Sanitized Audit Trail"** tab.
   - Review the chronological event log table.
   - Click **"Download Audit Trail (CSV)"**.
2. **Audit Verification:**
   - Open the generated CSV in Excel or a text editor.
   - Point out that only allowlisted metadata fields exist (`event_id`, `timestamp`, `event_type`, `stage`, `document_id`, `actor`, `details_entity_count`).
   - Search the file for customer names, SSNs, or emails: **0 matches found**.
3. **Presenter Narrative:**
   > *"Cadence's security and legal compliance requirements are satisfied: full operational traceability without creating a secondary PII honeypot in the logging subsystem."*

---

## 4. Live Automated Test Execution

To prove technical robustness to technical reviewers, run the comprehensive automated test suite live in terminal:

```powershell
pytest tests/unit tests/evaluation tests/integration tests/security -v
```

### Expected Output Summary
```text
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.1.1
collected 69 items

tests/unit/test_audit.py (4 passed)
tests/unit/test_errors.py (6 passed)
tests/unit/test_reporting.py (6 passed)
tests/unit/test_state.py (8 passed)
tests/unit/test_synthetic_generator.py (4 passed)
tests/unit/test_ui.py (6 passed)
tests/evaluation/test_metrics.py (10 passed)
tests/integration/test_orchestration.py (6 passed)
tests/security/test_artifact_access.py (11 passed)
tests/security/test_leakage.py (2 passed)
tests/security/test_release_gate.py (6 passed)

============================= 69 passed in 1.87s ==============================
```

---

## 5. Frequently Asked Questions (Demo Q&A)

**Q1: How does PII Guard prevent hallucinated spans or offset drift?**  
*Answer:* Ingestion runs a single-pass Unicode NFC normalizer. Character offsets generated during text extraction serve as the immutable single source of truth across detection, redaction, and evaluation.

**Q2: What happens if a detection engine crashes mid-document?**  
*Answer:* The pipeline catches all exceptions within the state manager, transitions cleanly to `FAILED`, logs a sanitized failure audit event, and denies release. No partially processed document is ever exported.

**Q3: Can an attacker guess artifact URLs or download another session's files?**  
*Answer:* No. Artifacts are indexed by opaque, random UUID tokens (`art-<uuid>`) stored in an isolated sandbox. Retrieval requires presenting both the artifact token and the owning `document_id`. Directory traversal characters (`..`, `/`, `\`) trigger immediate security exceptions.
