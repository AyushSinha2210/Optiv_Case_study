"""FastAPI HTTP API adapter for PII Guard document processing pipeline.

Preserves the existing architecture and delegates directly to existing backend modules:
- src.pii_guard.orchestration.pipeline.process_document
- src.pii_guard.ingestion.extractor.extract_document
- src.pii_guard.detection.detector.detect_pii
- src.pii_guard.redaction.policy.DEFAULT_POLICY
- src.pii_guard.orchestration.artifacts.get_default_artifact_manager
- src.pii_guard.reporting.report_generator.generate_report, generate_human_readable_summary
- src.pii_guard.reporting.audit.get_global_audit_trail
- src.pii_guard.reporting.export.export_to_json, export_to_csv
"""

import os
import sys
import tempfile
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

# Backend pipeline imports
from src.pii_guard.orchestration.pipeline import process_document
from src.pii_guard.orchestration.artifacts import get_default_artifact_manager
from src.pii_guard.orchestration.errors import sanitize_error_message
from src.pii_guard.orchestration.models import ProcessingResult
from src.pii_guard.ingestion.extractor import extract_document
from src.pii_guard.ingestion.config import IngestionConfig
from src.pii_guard.detection.detector import detect_pii
from src.pii_guard.redaction.policy import DEFAULT_POLICY
from src.pii_guard.reporting.audit import get_global_audit_trail
from src.pii_guard.reporting.report_generator import generate_report, generate_human_readable_summary
from src.pii_guard.reporting.export import export_to_json, export_to_csv

# TPRM Platform imports
from src.cadence_tprm.api import api_router as tprm_api_router
from src.cadence_tprm.database import engine as tprm_engine, Base as TPRMBase, SessionLocal as TPRMSessionLocal
from src.cadence_tprm.seed.seed_data import seed_database as seed_tprm_database

app = FastAPI(
    title="Cadence Enterprise Platform - TPRM & PII Guard",
    description="Unified Enterprise Platform for Cadence Financial Group: Third-Party Risk Management & Document Governance",
    version="1.0.0",
)

# Auto-initialize and seed TPRM database
try:
    TPRMBase.metadata.create_all(bind=tprm_engine)
    _db = TPRMSessionLocal()
    seed_tprm_database(_db)
    _db.close()
except Exception as e:
    print(f"TPRM Database initialization warning: {e}")

# Mount TPRM REST API
app.include_router(tprm_api_router)

# Enable CORS for Vite development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".text"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
ROOT_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = ROOT_DIR / "demo_samples" / "fixtures"
MANIFEST_PATH = ROOT_DIR / "demo_samples" / "manifest.json"

# In-memory cache of latest processed run details for UI document inspection
_DOC_CACHE: Dict[str, Dict[str, Any]] = {}


class ProcessResponse(BaseModel):
    document_id: str
    workflow_status: str
    current_stage: str
    stage_history: List[Dict[str, Any]]
    started_at: str
    completed_at: Optional[str]
    duration_sec: float
    source_type: Optional[str]
    pages_count: int
    char_count: int
    extraction_status: Optional[str]
    detection_status: Optional[str]
    redaction_status: Optional[str]
    verification_status: Optional[str]
    release_allowed: bool
    category_counts: Dict[str, int]
    redactions_applied: int
    safe_warnings: List[str]
    safe_error: Optional[str]
    safe_error_code: Optional[str]
    artifact_ref: Optional[str]
    extracted_text: Optional[str]
    redacted_text: Optional[str]
    entities: List[Dict[str, Any]]


class AssistantRequest(BaseModel):
    document_id: str
    query: Optional[str] = None
    topic: Optional[str] = "general"  # "decision", "taxonomy", "leakage", "policy", "general"


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "pii-guard-backend",
        "version": "1.0.0",
        "governance": "Cadence Financial Group",
        "pipeline_stages": [
            "RECEIVED", "VALIDATED", "EXTRACTED", "DETECTED", "REDACTED", "VERIFIED", "RELEASED"
        ],
    }


@app.get("/api/scenarios")
def list_scenarios():
    """Return certified deterministic demonstration scenarios."""
    scenarios = []
    if MANIFEST_PATH.exists():
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
                for fix in manifest_data.get("fixtures", []):
                    f_name = Path(fix["relative_path"]).name
                    f_path = FIXTURES_DIR / f_name
                    scenarios.append({
                        "id": fix.get("fixture_id"),
                        "name": fix.get("scenario", f_name),
                        "filename": f_name,
                        "file_type": fix.get("file_type"),
                        "description": fix.get("description"),
                        "expected_categories": fix.get("expected_categories", []),
                        "expected_count": fix.get("expected_entity_count", 0),
                        "size_bytes": f_path.stat().st_size if f_path.exists() else 0,
                    })
        except Exception:
            pass

    if not scenarios and FIXTURES_DIR.exists():
        for f in sorted(FIXTURES_DIR.glob("*.*")):
            scenarios.append({
                "id": f.stem,
                "name": f.name,
                "filename": f.name,
                "file_type": f.suffix.lstrip("."),
                "description": f"Fixture: {f.name}",
                "expected_categories": [],
                "expected_count": 0,
                "size_bytes": f.stat().st_size,
            })
    return {"scenarios": scenarios}


@app.post("/api/process", response_model=ProcessResponse)
async def process_document_endpoint(
    file: Optional[UploadFile] = File(None),
    scenario_filename: Optional[str] = Form(None),
    simulate_verification_failure: bool = Form(False),
):
    """Execute end-to-end PII protection pipeline on uploaded document or scenario fixture."""
    temp_path: Optional[Path] = None
    orig_name = "document.txt"

    try:
        if scenario_filename:
            # Clean filename to avoid path traversal
            safe_name = Path(scenario_filename).name
            fixture_path = FIXTURES_DIR / safe_name
            if not fixture_path.exists():
                raise HTTPException(status_code=404, detail=f"Scenario fixture '{safe_name}' not found.")
            orig_name = safe_name

            # Create temporary working copy
            suffix = fixture_path.suffix.lower()
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                temp_path = Path(tmp.name)
                tmp.write(fixture_path.read_bytes())

        elif file:
            orig_name = file.filename or "document.txt"
            suffix = Path(orig_name).suffix.lower()
            if suffix not in SUPPORTED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file extension '{suffix}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
                )

            contents = await file.read()
            if len(contents) > MAX_FILE_SIZE_BYTES:
                raise HTTPException(status_code=400, detail="File exceeds maximum allowed size of 50 MB.")
            if len(contents) == 0:
                raise HTTPException(status_code=400, detail="Uploaded file is 0 bytes (empty).")

            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                temp_path = Path(tmp.name)
                tmp.write(contents)
        else:
            raise HTTPException(status_code=400, detail="No file or scenario provided.")

        # Run authoritative backend pipeline
        options = {"simulate_verification_failure": simulate_verification_failure}
        res: ProcessingResult = process_document(str(temp_path), options=options)

        # Retrieve extracted text and entities for UI inspection
        extracted_text = ""
        entities_data: List[Dict[str, Any]] = []
        try:
            cfg = IngestionConfig.from_env()
            ext_doc = extract_document(str(temp_path), config=cfg)
            extracted_text = ext_doc.text
            det_res = detect_pii(ext_doc)
            for ent in det_res.entities:
                val = extracted_text[ent.start:ent.end] if ent.end <= len(extracted_text) else ""
                masked = DEFAULT_POLICY.get(ent.type.upper(), f"[REDACTED_{ent.type}]")
                entities_data.append({
                    "type": ent.type,
                    "start": ent.start,
                    "end": ent.end,
                    "confidence": ent.confidence,
                    "value": val,
                    "masked_value": masked,
                })
        except Exception:
            pass

        # Retrieve redacted text if release is allowed
        redacted_text = None
        if res.release_allowed and res.artifact_ref:
            try:
                art_mgr = get_default_artifact_manager()
                content_bytes = art_mgr.read_artifact_bytes(res.artifact_ref, res.document_id, True)
                redacted_text = content_bytes.decode("utf-8", errors="replace")
            except Exception:
                pass

        # Calculate stage durations
        stage_history_payload = []
        prev_dt = res.started_at
        for idx, t in enumerate(res.stage_history):
            cur_dt = t.timestamp
            dur = max(0.0, (cur_dt - prev_dt).total_seconds())
            stage_history_payload.append({
                "step": idx + 1,
                "from_stage": t.from_stage.value if t.from_stage else "INITIAL",
                "to_stage": t.to_stage.value,
                "timestamp": cur_dt.isoformat(),
                "duration_sec": round(dur, 4),
                "message": t.message or "Stage transition complete",
            })
            prev_dt = cur_dt

        tot_duration = (
            (res.completed_at - res.started_at).total_seconds()
            if res.completed_at
            else 0.0
        )

        response_payload = {
            "document_id": res.document_id,
            "workflow_status": res.workflow_status,
            "current_stage": res.current_stage.value,
            "stage_history": stage_history_payload,
            "started_at": res.started_at.isoformat(),
            "completed_at": res.completed_at.isoformat() if res.completed_at else None,
            "duration_sec": round(tot_duration, 4),
            "source_type": res.source_type,
            "pages_count": res.pages_count,
            "char_count": res.char_count,
            "extraction_status": res.extraction_status,
            "detection_status": res.detection_status,
            "redaction_status": res.redaction_status,
            "verification_status": res.verification_status,
            "release_allowed": res.release_allowed,
            "category_counts": dict(res.category_counts),
            "redactions_applied": res.redactions_applied,
            "safe_warnings": list(res.safe_warnings),
            "safe_error": res.safe_error,
            "safe_error_code": res.safe_error_code,
            "artifact_ref": res.artifact_ref,
            "extracted_text": extracted_text,
            "redacted_text": redacted_text,
            "entities": entities_data,
        }

        # Cache for reporting & assistant Q&A
        _DOC_CACHE[res.document_id] = {
            "result": res,
            "payload": response_payload,
            "orig_filename": orig_name,
        }

        return ProcessResponse(**response_payload)

    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass


@app.get("/api/artifact/{document_id}")
def download_artifact(document_id: str):
    """Controlled artifact download endpoint with strict fail-closed release gate enforcement."""
    cached = _DOC_CACHE.get(document_id)
    if not cached:
        raise HTTPException(status_code=404, detail="Document not found or session expired.")

    res: ProcessingResult = cached["result"]
    if not res.release_allowed or res.verification_status != "PASS" or not res.artifact_ref:
        raise HTTPException(
            status_code=403,
            detail="Release gate BLOCKED: Document failed independent verification or release is unauthorized.",
        )

    art_mgr = get_default_artifact_manager()
    try:
        data = art_mgr.read_artifact_bytes(res.artifact_ref, res.document_id, res.release_allowed)
        ext = res.source_type if res.source_type in ("txt", "docx") else "txt"
        orig_name = cached.get("orig_filename", "document")
        clean_name = f"redacted_{Path(orig_name).stem}.{ext}"
        return Response(
            content=data,
            media_type="text/plain" if ext == "txt" else "application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{clean_name}"'},
        )
    except Exception as ex:
        raise HTTPException(status_code=500, detail=sanitize_error_message(str(ex)))


@app.get("/api/report/{document_id}")
def get_report(document_id: str, format: str = Query("json", pattern="^(json|summary|csv)$")):
    """Retrieve Contract D compliance report in JSON, CSV, or executive summary text format."""
    cached = _DOC_CACHE.get(document_id)
    if not cached:
        raise HTTPException(status_code=404, detail="Document not found.")

    res: ProcessingResult = cached["result"]
    report = generate_report(res)

    if format == "summary":
        summary_text = generate_human_readable_summary(report)
        return PlainTextResponse(summary_text)
    elif format == "csv":
        csv_data = export_to_csv(report)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="pii_report_{document_id}.csv"'},
        )
    else:
        json_data = export_to_json(report)
        return Response(
            content=json_data,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="pii_report_{document_id}.json"'},
        )


@app.get("/api/audit/{document_id}")
def get_audit_trail(document_id: str):
    """Retrieve immutable, metadata-only sanitized audit trail."""
    trail = get_global_audit_trail()
    events = trail.export_sanitized_log(document_id)
    return {"document_id": document_id, "events": events}


@app.post("/api/assistant/chat")
def assistant_chat(req: AssistantRequest):
    """AI-powered security assistant explaining technical decisions, verification, and architecture."""
    cached = _DOC_CACHE.get(req.document_id)
    if not cached:
        raise HTTPException(status_code=404, detail="Document not found.")

    payload = cached["payload"]
    res: ProcessingResult = cached["result"]
    query = (req.query or "").strip().lower()
    topic = req.topic or "general"

    # Dynamic explanation generation using real telemetry and governance policy
    is_released = res.release_allowed and res.verification_status == "PASS"
    cat_counts = payload["category_counts"]
    total_ents = sum(cat_counts.values())

    explanation = ""
    citations = []

    if "decision" in query or topic == "decision" or "why" in query and "block" in query or "why" in query and "release" in query:
        if is_released:
            explanation = (
                f"### ✅ Release Gate Authorization: GRANTED\n\n"
                f"- **Dual-Key Barrier Assessment:** The pipeline evaluated two strict prerequisites: (1) Independent verification status is `PASS`, and (2) release authorization flag is `True`.\n"
                f"- **Residual PII Re-scan:** Member 3's independent verification engine re-examined the generated artifact text and found **0 residual leaks** across all regex, structural, and known-entity checks.\n"
                f"- **Entity Masking:** All {total_ents} detected sensitive entities were masked right-to-left using contextual tokens (`<CATEGORY>` / `[REDACTED_...]`).\n"
                f"- **Download Status:** Client download is authorized under Cadence Financial Group AI Governance Policy."
            )
        else:
            reason = payload.get("safe_error") or "Verification failed or incomplete"
            explanation = (
                f"### 🛑 Release Gate Authorization: BLOCKED\n\n"
                f"- **Fail-Closed Gate Triggered:** The document was withheld because `verification_status` returned `{res.verification_status}`.\n"
                f"- **Root Cause:** {reason}.\n"
                f"- **Security Invariant:** Under the Zero-Leakage Mandate, unredacted or unverified document egress to downstream LLMs is mathematically prohibited.\n"
                f"- **Protection Applied:** Artifact reference token was invalidated, and client download is strictly disabled."
            )
        citations = ["src/pii_guard/redaction/gate.py", "src/pii_guard/orchestration/pipeline.py:L245-265"]

    elif "taxonomy" in query or "detection" in query or topic == "taxonomy" or "entities" in query:
        breakdown = ", ".join(f"**{k}**: {v}" for k, v in cat_counts.items()) if cat_counts else "None"
        explanation = (
            f"### 📊 PII Detection & Classification Breakdown\n\n"
            f"- **Detected Categories:** {breakdown}\n"
            f"- **Total Entities Flagged:** {total_ents}\n"
            f"- **Detection Rules Applied:**\n"
            f"  - **Deterministic Regex Matchers:** Validated patterns with checksum algorithms (e.g., Luhn check for Credit Cards, area/group checks for SSN, holder-type codes for Indian PAN).\n"
            f"  - **Overlap & Precedence Resolution:** Candidate spans are sorted by precedence (Government ID / Cards > Email / Employee ID > IP > Phone > Person). In nested occurrences, the higher precedence span claims the token.\n"
            f"  - **Page Boundary Safety:** Zero spans cross document form-feed (`\\f`) markers."
        )
        citations = ["src/pii_guard/detection/pattern_detector.py", "src/pii_guard/detection/classifier.py"]

    elif "leak" in query or "verification" in query or topic == "leakage":
        explanation = (
            f"### 🔍 Independent Verification & Secondary Re-scan\n\n"
            f"- **Independent Verification Plane:** Redaction verification does not rely on the detection engine. It executes an autonomous secondary scanner across the saved artifact.\n"
            f"- **Checks Performed:**\n"
            f"  1. **Known Value Matching:** Verifies that no original unmasked values from the detection stage remain in the output.\n"
            f"  2. **Residual Pattern Scanning:** Runs independent regex passes for phone numbers, email addresses, government IDs, Luhn-valid cards, and IP addresses.\n"
            f"  3. **Structure Retention Scoring:** Validates that line breaks, headings, and paragraph boundaries were preserved.\n"
            f"- **Current Verification Status:** `{res.verification_status}`"
        )
        citations = ["src/pii_guard/redaction/verifier.py:L52-85", "src/pii_guard/redaction/service.py"]

    elif "audit" in query or "policy" in query or topic == "policy":
        explanation = (
            f"### 📜 Cadence Financial Zero-Leakage Audit Policy\n\n"
            f"- **Immutable Audit Trail:** All pipeline lifecycle transitions (`RECEIVED` through `RELEASED`) are atomically logged.\n"
            f"- **Metadata-Only Projection:** Strict allowlist serialization guarantees that **zero raw document text** and **zero detected PII values** are written to audit records or Contract D JSON/CSV exports.\n"
            f"- **Cryptographic Sandboxing:** Protected artifacts are isolated in temporary sandbox storage addressed by opaque UUID tokens (`art-<uuid>`), preventing directory traversal attacks."
        )
        citations = ["src/pii_guard/reporting/audit.py", "src/pii_guard/orchestration/artifacts.py"]

    else:
        # General response tailored to current document run
        status_banner = "✅ Authorized for Downstream LLMs" if is_released else "🛑 Blocked / Withheld"
        explanation = (
            f"### 🛡️ PII Guard Executive Assistant Summary\n\n"
            f"- **Document ID:** `{res.document_id}`\n"
            f"- **Outcome:** **{status_banner}** (Workflow: `{res.workflow_status.upper()}`)\n"
            f"- **Format & Scale:** `{res.source_type or 'unknown'}` format | {res.pages_count} pages | {res.char_count} characters\n"
            f"- **Entities Masked:** {res.redactions_applied} PII spans across {len(cat_counts)} categories\n"
            f"- **Verification Gate:** Status `{res.verification_status}` | Release Allowed: `{res.release_allowed}`\n"
            f"- **Processing Duration:** {payload['duration_sec']} seconds across all 7 pipeline stages.\n\n"
            f"You can ask me questions about **Release Decisions**, **PII Classifications**, **Verification Re-scans**, or **Audit Compliance**."
        )
        citations = ["src/pii_guard/orchestration/pipeline.py", "docs/security.md"]

    return {
        "document_id": req.document_id,
        "query": req.query,
        "topic": topic,
        "explanation": explanation,
        "citations": citations,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Mount built frontend if available
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
