# Member 5 & Member 4 Commit Log: PII Guard
### Cadence Financial Group — Cyber Strategy & AI Governance Case Study

This log records every incremental Git commit created during the implementation of Member 5 (Tirth: Orchestration, UI, Audit & Integration) and Member 4 (Nancy: Coding Deliverables — Synthetic Fixtures & Evaluation).

---

## Commit History

| Commit Hash | Commit Message | Files Changed | Implementation Completed | Tests Executed & Results | Known Limitations |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `e62ebde` | `docs(member5): add implementation plan and initial commit log` | `docs/member5_member4_implementation_plan.md`<br>`docs/member5_member4_commit_log.md` | Phase 0 repository inspection, architecture mapping, and phase-by-phase implementation roadmap. | Static inspection & Markdown validation: **PASS** | Initial planning stage; no executable code changes. |
| `925dbf6` | `feat(orchestration): define pipeline states, error hierarchy, and integration contracts` | `src/pii_guard/orchestration/state.py`<br>`src/pii_guard/orchestration/errors.py`<br>`src/pii_guard/orchestration/models.py`<br>`tests/unit/test_state.py`<br>`tests/unit/test_errors.py` | Finite state machine (`PipelineStage`, `PipelineStateManager`), legal transition validator, sanitized error hierarchy (`sanitize_error_message`), Contracts B, C, D models and `ProcessingResult`. | `pytest tests/unit/test_state.py tests/unit/test_errors.py`<br>**14 passed in 0.17s** | Standalone models awaiting pipeline coordinator integration. |
| `532a4a1` | `feat(reporting): implement sanitized audit trail subsystem and leakage guard` | `src/pii_guard/reporting/audit.py`<br>`tests/unit/test_audit.py` | Thread-safe `AuditTrail`, immutable `AuditEvent`, strict allowlist projection filtering sensitive keys and raw text, atomic `relink_document_id`. | `pytest tests/unit/test_audit.py`<br>**4 passed in 0.08s** | In-memory store; persistent database backend out of project scope. |
| `3beed11` | `feat(reporting): generate structured reports and allowlist-sanitized exports` | `src/pii_guard/reporting/report_generator.py`<br>`src/pii_guard/reporting/export.py`<br>`tests/unit/test_reporting.py` | Contract D JSON report generator, human-readable executive summary, allowlisted JSON and CSV file exporters with zero-leakage guard. | `pytest tests/unit/test_reporting.py`<br>**6 passed in 0.09s** | Reports rely on upstream stage outputs. |
| `4acb41f` | `feat(evaluation): implement bipartite matching detection metrics and edge case handling` | `src/pii_guard/reporting/metrics.py`<br>`tests/evaluation/test_metrics.py` | Member 4 evaluation metrics engine (`evaluate_predictions`), TP/FP/FN counts, Precision, Recall, F1, FNR, exact, overlap, and IoU $\ge 0.50$ matching, zero-denominator rules, per-category breakdown. | `pytest tests/evaluation/test_metrics.py`<br>**10 passed in 0.09s** | Evaluates character-offset boundaries on normalized text. |
| `dfdf812` | `feat(demo): implement deterministic synthetic sample generator and test fixtures` | `demo_tools/generate_synthetic_samples.py`<br>`demo_samples/*`<br>`tests/unit/test_synthetic_generator.py` | Seeded deterministic generator producing 10 realistic scenarios (customer email, loan, wire, medical, board briefing, dispute, clean, high-density, edge cases, malformed), ground-truth `manifest.json`. | `pytest tests/unit/test_synthetic_generator.py`<br>**4 passed in 0.08s** | Synthetic entities generated with test ranges and faker templates. |
| `3f075a1` | `feat(security): implement controlled artifact sandbox and path traversal guard` | `src/pii_guard/orchestration/artifacts.py`<br>`tests/security/test_artifact_access.py` | Opaque random UUID tokens (`art-<uuid>`), sandbox storage isolation, strict path traversal rejection (`..`, `/`, `\`, `\x00`), ownership binding to document ID. | `pytest tests/security/test_artifact_access.py`<br>**11 passed in 0.12s** | Session-scoped ephemeral token registry. |
| `59f4046` | `feat(orchestration): implement pipeline coordinator and fail-closed release gate` | `src/pii_guard/detection/detector.py`<br>`src/pii_guard/redaction/redactor.py`<br>`src/pii_guard/orchestration/pipeline.py`<br>`tests/integration/test_orchestration.py` | 7-stage coordinator (`process_document`), ingestion integration (`extract_document`), Presidio/regex detection reference, contextual token redaction, secondary verification re-scan, fail-closed release barrier (`PASS` AND `release_allowed == True`). | `pytest tests/integration/test_orchestration.py`<br>**6 passed in 0.98s** | OCR for scanned image PDFs requires local Tesseract binary on OS PATH; native documents process directly. |
| `6dd29d7` | `feat(ui): implement Streamlit application with fail-closed download barriers` | `app.py`<br>`tests/unit/test_ui.py` | Streamlit interactive web interface with upload validator, progress indicators, side-by-side redaction preview, KPI cards, audit/report tabs, conditionally gated download buttons. | `pytest tests/unit/test_ui.py`<br>**6 passed in 0.14s** | Web application designed for interactive analysts and demonstration. |
| `4f7700c` | `test(security): add fail-closed release gate invariants and canary leakage regression tests` | `tests/security/test_release_gate.py`<br>`tests/security/test_leakage.py` | 6 release gate invariant tests covering FAIL, INCOMPLETE, exception abort, and tamper attempts; 2 canary leakage tests verifying zero secret token leakage in reports, audit events, exports, and manifests. | `pytest tests/security/test_release_gate.py tests/security/test_leakage.py`<br>**8 passed in 0.16s** (Full suite: **69 passed**) | Synthetic canary strings verify schema serialization guarantees. |
| `[Phase 10]` | `docs(member5): finalize architecture, security, evaluation, demo script, and commit log` | `docs/architecture.md`<br>`docs/security.md`<br>`docs/evaluation.md`<br>`docs/demo_script.md`<br>`README.md`<br>`docs/member5_member4_commit_log.md`<br>`docs/member5_member4_implementation_plan.md` | Author comprehensive architecture, security threat model, evaluation metrics guide, live demonstration script, updated README with Member 5 & Member 4 deliverables, and finalized commit log. | Full test suite regression:<br>`pytest tests/unit tests/evaluation tests/integration tests/security`<br>**69 passed in 1.87s** | Nancy presentation slides (.pptx) developed separately. |

---

## Test Execution Summary

The entire Member 5 and Member 4 automated test suite executes cleanly under Python 3.13:

```text
============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.1.1
rootdir: D:\Dev_Projects\Optive_Case_study
collected 69 items

tests/unit/test_audit.py ................ [ 4 passed]
tests/unit/test_errors.py ............... [ 6 passed]
tests/unit/test_reporting.py ............ [ 6 passed]
tests/unit/test_state.py ................ [ 8 passed]
tests/unit/test_synthetic_generator.py .. [ 4 passed]
tests/unit/test_ui.py .................. [ 6 passed]
tests/evaluation/test_metrics.py ........ [10 passed]
tests/integration/test_orchestration.py . [ 6 passed]
tests/security/test_artifact_access.py .. [11 passed]
tests/security/test_leakage.py .......... [ 2 passed]
tests/security/test_release_gate.py ..... [ 6 passed]

============================= 69 passed in 1.87s ==============================
```
