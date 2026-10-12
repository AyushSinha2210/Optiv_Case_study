# PII Guard — Shared Interface Contracts & Pipeline Protocols
**Specification Document:** Section 10 Contract Reference  
**Applicability:** Members 1–5 (Ayush Sinha, Avishi Sharma, Yash, Nancy, Tirth)

---

## Overview

The point of a contract is to allow each member to develop and test their module independently using typed structures and deterministic mock data. 

All modules use Pydantic v2 / typed models matching the exact schemas defined below.

---

## Contract A: `ExtractedDocument` (Member 1: Ayush Sinha ──> Member 2: Avishi Sharma)

The output of the Ingestion module and the single source of truth for all downstream operations:

```json
{
  "document_id": "doc-001",
  "source_type": "pdf|scanned_pdf|docx|pptx|txt",
  "text": "exact extracted text",
  "pages": [
    {
      "index": 1,
      "label": "page|slide",
      "start": 0,
      "end": 248,
      "method": "native|ocr|mixed",
      "ocr_confidence": 94.2,
      "char_count": 248,
      "warnings": []
    }
  ],
  "warnings": [
    {
      "code": "WARN_OCR_LOW_CONFIDENCE",
      "page": 1,
      "message": "Mean OCR confidence below threshold"
    }
  ],
  "extraction_status": "success|partial|failed"
}
```

### Contract Rules for Contract A:
1. `document_id`: A unique string identifier assigned per request to prevent cross-document contamination.
2. `text`: **Single source of truth.** Downstream modules MUST NOT modify, trim, re-encode, or re-normalize this string.
3. `start` and `end`: Zero-based, end-exclusive character offsets into `text`. For any page $i$, `text[pages[i].start : pages[i].end]` recovers that page's text.
4. Pages are separated by a form feed (`\f`, `U+000C`). Downstream entity matches must not cross `\f` boundaries.

---

## Contract B: `DetectionResult` (Member 2: Avishi Sharma ──> Member 3: Yash)

The output of the PII Detection and Classification module:

```json
{
  "document_id": "doc-001",
  "entities": [
    {
      "type": "EMAIL",
      "start": 12,
      "end": 29,
      "confidence": 0.98
    }
  ],
  "warnings": []
}
```

### Contract Rules for Contract B:
1. `entities`: List of classified PII spans. Each span has:
   - `type`: Standard taxonomy label (`PERSON`, `EMAIL`, `PHONE`, `ADDRESS`, `GOVERNMENT_ID`, `FINANCIAL_IDENTIFIER`, `IP_ADDRESS`, `EMPLOYEE_ID`).
   - `start`: 0-based start offset into `ExtractedDocument.text`.
   - `end`: 0-based end offset (exclusive) into `ExtractedDocument.text`.
   - `confidence`: Calibrated score (float between `0.0` and `1.0`).
2. Overlap Resolution: If deterministic regex and contextual NER overlap, `classifier.py` deterministically selects the higher-precedence entity.

---

## Contract C: `RedactionResult` (Member 3: Yash ──> Member 5: Tirth)

The output of the Redaction, Verification, and Release Gate module:

```json
{
  "document_id": "doc-001",
  "artifact_ref": "private reference, not a public file path",
  "redactions_applied": 1,
  "verification_status": "PASS|FAIL|INCOMPLETE",
  "release_allowed": false,
  "findings": []
}
```

### Contract Rules for Contract C:
1. `verification_status`:
   - `PASS`: All detected PII was safely redacted; post-redaction re-scan found 0 leakage.
   - `FAIL`: Leakage detected during artifact verification; unsafe to release.
   - `INCOMPLETE`: Required verification could not run or was interrupted.
2. `release_allowed`: Boolean flag. Must be strictly `True` for Tirth's UI to enable client download.
3. `artifact_ref`: An opaque token or controlled internal storage path. **Never expose raw filesystem paths to web clients.**

---

## Contract D: `ProcessingReport` (Member 5: Tirth ──> Client / Audit)

The final audit report assembled by the Orchestration and Reporting module:

```json
{
  "document_id": "doc-001",
  "workflow_status": "success|blocked|failed",
  "category_counts": {
    "PERSON": 2,
    "EMAIL": 1,
    "GOVERNMENT_ID": 1
  },
  "verification_status": "PASS|FAIL|INCOMPLETE",
  "created_at": "2026-10-12T09:00:00Z",
  "module_versions": {
    "ingestion": "1.0.0",
    "detection": "1.0.0",
    "redaction": "1.0.0"
  }
}
```

### Contract Rules for Contract D:
1. **Privacy Mandate:** Contains exclusively metadata, timestamps, entity counts by category, and status flags.
2. **Zero Leakage:** Strictly contains NO raw document text, NO matched entity values, and NO customer PII.
