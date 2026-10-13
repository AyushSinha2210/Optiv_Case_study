# PII Guard: Security Architecture, Threat Model & Invariants
### Cadence Financial Group — Cyber Strategy & AI Governance Case Study
**Security Ownership:** Tirth (Member 5: Orchestration, Release Gate, Audit & Sandbox) & Yash (Member 3: Redaction & Verification)

---

## 1. Security Overview & Philosophy

In the context of Cadence Financial Group, document processing before LLM dissemination represents a critical defensive perimeter. A single unmasked Social Security Number (SSN), bank account number, or health record could violate GLBA, GDPR, or HIPAA regulations, resulting in substantial regulatory penalties and reputational damage.

The **PII Guard** security architecture is founded upon the principle of **Fail-Closed Security by Default**:
- When in doubt, block release.
- If any component raises an exception, abort and quarantine.
- If verification is incomplete or skipped, withhold the artifact.
- Zero raw data crosses the boundary into telemetry, logs, or reports.

---

## 2. Threat Model

We evaluated five primary threat vectors against the document processing pipeline:

| Threat ID | Threat Vector | Description | Potential Impact | Mitigation Strategy |
| :---: | :--- | :--- | :--- | :--- |
| **THREAT-01** | **Audit & Log Data Leakage** | Raw PII or unredacted document fragments logged in application logs, audit trails, or exported CSV reports. | Permanent retention of PII in observability tools (Splunk/ELK), violating data minimization. | Strict allowlist projection in `AuditEvent`, `ProcessingReport`, and CSV export. Raw text fields are completely excluded. |
| **THREAT-02** | **Path Traversal & Jail Escape** | Malicious users exploit file path parameters (e.g., `../../etc/passwd` or `..\Windows\win.ini`) to exfiltrate system files or unredacted quarantine files. | Arbitrary file read; access to other users' sensitive raw uploads. | Opaque UUID tokens (`art-<uuid>`) registered in an isolated sandbox. Immediate rejection of delimiters (`/`, `\`), `..`, and null bytes (`\x00`). |
| **THREAT-03** | **Release Gate Bypass** | Attackers intercept or tamper with the verification outcome to download unredacted or partially redacted files. | Exfiltration of unredacted PII to external LLM agents. | Dual-condition gate: `verification_status == "PASS"` AND `release_allowed == True`. UI download button dynamically disabled when blocked. |
| **THREAT-04** | **Denial of Service / Zip Bombs** | Attackers upload nested archives or oversized files with high compression ratios ($\ge 100:1$) to exhaust server memory. | Application downtime, crash of worker processes. | Ingestion layer magic byte sniffing, file size bounds ($\le 50\text{ MB}$), and decompression ratio limits. |
| **THREAT-05** | **Error Trace Leakage** | Uncaught exceptions print filesystem paths, stack frames with sensitive variable values, or user inputs to the user interface. | Information disclosure of internal host architecture or user PII. | Sanitized error hierarchy (`sanitize_error_message`), regex stripping of Windows/POSIX paths, emails, phones, and SSNs. |

---

## 3. Core Security Invariants

The following security invariants are mathematically and procedurally enforced across all modules:

### Invariant 1: Fail-Closed Dual-Key Release Barrier
$$\text{Artifact Egress Granted} \iff (\text{verification\_status} = \text{"PASS"}) \land (\text{release\_allowed} = \text{True})$$
If either term evaluates to false, or if an unhandled exception occurs at any point in the pipeline:
1. `release_allowed` is forced to `False`.
2. State transitions to `BLOCKED` or `FAILED`.
3. No artifact token is generated.
4. Downstream download buttons are disabled.

### Invariant 2: Zero Canary Leakage in Observability
No raw document text, entity string value, or canary token may ever appear in:
- `AuditEvent.details`
- `ProcessingReport` JSON representation
- Audit Trail CSV exports
- Application exception messages

### Invariant 3: Opaque Artifact Isolation
All released documents are stored within a controlled `ArtifactSandbox`:
- Files are named by cryptographic UUID tokens (`art-<uuid>`).
- Direct file paths are never exposed to the client or frontend.
- Tokens are bound to the specific `document_id`. Replaying a token with a different document ID results in `ArtifactSecurityError`.
- Symlink escapes and directory transversal attempts are validated with `os.path.realpath` against the sandbox base path.

### Invariant 4: Input Validation Before Processing
Every incoming file must pass validation:
- Supported extensions: `.pdf`, `.docx`, `.pptx`, `.txt`.
- Content length $> 0$ bytes and $\le 50$ MB.
- Magic bytes must match expected file signatures (preventing renamed `.exe` or shell scripts).

---

## 4. Leakage Guard & Error Sanitization Implementation

### Allowlist Serialization
In `src/pii_guard/reporting/audit.py`, `AuditEvent` does not accept arbitrary dictionaries without filtering:
```python
SAFE_KEYS = {"entity_count", "categories", "pages", "file_type", "status", "processing_time_ms"}
sanitized_details = {k: v for k, v in raw_details.items() if k in SAFE_KEYS and not isinstance(v, (str, bytes))}
```
Any key matching `text`, `raw_text`, `entity_value`, or containing strings matching PII formats is discarded.

### Error Message Sanitizer
In `src/pii_guard/orchestration/errors.py`, all exceptions raised through `PipelineError` pass their messages through `sanitize_error_message()`:
```python
def sanitize_error_message(msg: str) -> str:
    # Strips Windows paths (e.g. C:\Users\...)
    msg = re.sub(r"[A-Za-z]:\\[\w\s\-.\\]+", "[PATH_REDACTED]", msg)
    # Strips POSIX paths (e.g. /etc/...)
    msg = re.sub(r"/(?:[\w.-]+/)+[\w.-]+", "[PATH_REDACTED]", msg)
    # Strips email patterns
    msg = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[EMAIL_REDACTED]", msg)
    # Strips phone numbers
    msg = re.sub(r"\b(?:\+?1[-.]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE_REDACTED]", msg)
    # Strips SSN patterns
    msg = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[SSN_REDACTED]", msg)
    return msg
```

---

## 5. Member 3 Redaction, Verification & Structure Preservation

### Rules
- Detection offsets are zero-based and end-exclusive into the exact extracted text.
- Unknown, invalid, out-of-range, and overlapping spans are rejected.
- Replacements are applied from the highest offset to the lowest.
- Findings never contain raw document text, matched values, or source snippets.
- Verification checks both known detected values and independent residual patterns.
- The saved artifact must be reopened by a format-specific reader before `PASS`.
- Missing or failed verification means `release_allowed=False`.
- Only synthetic values may be committed to tests and fixtures.

### Saved Artifact Verification
`redact_and_validate()` accepts `artifact_ref` and `artifact_text_reader`. The reader must reopen the actual saved output and extract its text. For PDF, covering text with a black rectangle is not sufficient: the original text must not remain selectable or extractable. PDF/DOCX/PPTX adapters should also check supported hidden layers, comments, and metadata.

### Structure Score
The included score checks line boundaries and heading counts. Format adapters can add page, paragraph, table, or slide checks before claiming full structure preservation.

### Known Limitation
No verifier can prove that every possible PII value was detected. Missed names, addresses, or unusual identifiers remain residual risk and must be documented.

---

## 6. Security & Invariant Automated Verification

Our test suite enforces these invariants through automated regression tests:

1. **`tests/security/test_release_gate.py` (6 Invariant Tests):**
   - Asserts artifact access denied when verification status is `FAIL`.
   - Asserts artifact access denied when verification status is `INCOMPLETE`.
   - Asserts artifact access denied when `release_allowed` is `False`, even if verification status is `PASS`.
   - Asserts pipeline fail-closed behavior when verification raises an unhandled exception.
   - Asserts early stage failure blocks release immediately.
   - Asserts reporting objects alone cannot generate or leak artifact tokens.

2. **`tests/security/test_leakage.py` (2 Canary Tests):**
   - Generates canary strings: `canary.user@secret-domain.corp`, `CANARY-SSN-000-12-3456`, `CANARY-ACCT-9876543210`.
   - Executes pipeline and serializes `ProcessingReport`, `AuditEvent`, and CSV exports.
   - Asserts **zero occurrences** of any canary substring across all serialized metadata.
   - Asserts synthetic manifest fixtures contain zero canary leakage.

3. **`tests/security/test_artifact_access.py` (11 Traversal Tests):**
   - Tests path traversal payloads: `../secret.txt`, `..\secret.txt`, `/etc/passwd`, `C:\Windows\System32\cmd.exe`, `art-123\x00malicious`, `art-123/../../etc/passwd`.
   - Verifies all payloads raise `ArtifactSecurityError` before executing filesystem queries.

<<<<<<< HEAD
---

## 6. Member 3 Security Notes & Release-Gate Handshake

Member 3 owns deterministic redaction, verification, leakage testing,
structure-preservation checks, and the fail-closed release gate.

### Rules

- Detection offsets are zero-based and end-exclusive into the exact extracted text.
- Unknown, invalid, out-of-range, and overlapping spans are rejected.
- Replacements are applied from the highest offset to the lowest.
- Findings never contain raw document text, matched values, or source snippets.
- Verification checks both known detected values and independent residual patterns.
- The saved artifact must be reopened by a format-specific reader before `PASS`.
- Missing or failed verification means `release_allowed=False`.
- Only synthetic values may be committed to tests and fixtures.

### Saved Artifact Verification

`redact_and_validate()` accepts `artifact_ref` and `artifact_text_reader`. The
reader must reopen the actual saved output and extract its text. For PDF,
covering text with a black rectangle is not sufficient: the original text must
not remain selectable or extractable. PDF/DOCX/PPTX adapters should also check
supported hidden layers, comments, and metadata.

The current module intentionally does not pretend to implement format-specific
export/redaction adapters. It provides the security boundary where those
adapters are connected.

### Structure Score

The included score checks line boundaries and heading counts. It is not a
complete PDF, DOCX, or PPTX layout score. Format adapters must add page,
paragraph, table, or slide checks before claiming full structure preservation.

### Known Limitation

No verifier can prove that every possible PII value was detected. Missed names,
addresses, or unusual identifiers remain residual risk and must be documented.

### Test Command

```bash
pytest -q tests/test_redaction.py
```
=======
4. **`tests/test_redaction.py` (Member 3 Verification Tests):**
   - Verifies right-to-left span replacements, out-of-range rejection, overlap rejection, unknown category rejection, and reopened clean artifact release gating.
>>>>>>> origin/feature/member5-integration
