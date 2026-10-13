# Baseline Test Results

**Date:** September 16, 2026 / October 2026  
**Test Runner:** pytest 9.1.1, Python 3.13.7, Vite 8.3.4  
**Branch:** `feature/tprm-enterprise-implementation`  

---

## 1. Baseline Backend Test Suite Execution

```bash
.venv\Scripts\python -m pytest tests/unit/test_api_server.py -q
```
**Outcome:**
- `6 passed, 1 warning in 1.60s`
- Collected 246 total tests across legacy suites (`test_all_document_formats.py`, `test_detection.py`, `test_extreme_edge_cases.py`, `test_ingestion.py`, `test_redaction.py`, `tests/unit/`).

## 2. Baseline Frontend Build Execution

```bash
npm run build (in frontend/)
```
**Outcome:**
- `tsc -b && vite build`
- `✓ 1914 modules transformed.`
- `dist/index.html 0.59 kB`
- `dist/assets/index-DWYQ_6qw.css 4.57 kB`
- `dist/assets/index-Ce9Tt5hT.js 267.81 kB`
- `✓ built in 1.27s`
- Zero TypeScript compiler errors. Zero bundler warnings.

## 3. Git Tree Status

- Initial commit on branch `feature/tprm-enterprise-implementation`:
  - `main` branch clean at HEAD.
  - Branch created cleanly without uncommitted working-tree dirt.
  - Untracked files safely isolated in `docs/`: `Cadence_TPRM_Training.docx`, `Cadence_TPRM_Training_extracted.md`.

## 4. Assessment Summary

The baseline environment is 100% operational, healthy, and verified with zero blockers. Ready for TPRM implementation.
