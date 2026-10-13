"""FastAPI HTTP API server for OPTIV Document Privacy, PII Detection, Redaction, and Audit Workspace.

Preserves the existing architecture and integrates:
- src.pii_guard.orchestration.pipeline.process_document
- src.pii_guard.ingestion.extractor.extract_document
- src.pii_guard.detection.detector.detect_pii
- src.pii_guard.redaction.policy.DEFAULT_POLICY
- src.pii_guard.orchestration.artifacts.get_default_artifact_manager
- src.pii_guard.reporting.report_generator.generate_report, generate_human_readable_summary
- src.pii_guard.reporting.audit.get_global_audit_trail
- src.pii_guard.reporting.export.export_to_json, export_to_csv
- src.pii_guard.persistence: persistent processing runs, findings, audit records, metrics
- src.pii_guard.redaction.native_redactors: PDF, PPTX, JSON, Image format-aware sanitization
- src.cadence_tprm: TPRM REST APIs and database models
"""

import os
import sys
import tempfile
import json
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response, Query, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse
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
from src.pii_guard.redaction.native_redactors import (
    redact_native_pdf,
    redact_native_pptx,
    redact_native_json,
    redact_native_image,
)
from src.pii_guard.persistence import (
    init_pii_guard_db,
    save_processing_run,
    get_processing_run,
    list_processing_runs,
    list_findings,
    update_finding_status,
    list_audit_records,
    get_overview_metrics,
)

# TPRM Platform imports
from src.cadence_tprm.api import api_router as tprm_api_router
from src.cadence_tprm.database import (
    engine as tprm_engine,
    Base as TPRMBase,
    SessionLocal as TPRMSessionLocal,
    init_db as init_tprm_db,
)
from src.cadence_tprm.seed.seed_data import seed_database as seed_tprm_database

app = FastAPI(
    title="OPTIV Document Privacy & PII Protection Workspace",
    description="Enterprise Document Privacy, PII Detection, Redaction, Verification, and Audit Platform",
    version="2.0.0",
)

# Auto-initialize and seed databases
try:
    init_tprm_db(tprm_engine)
    init_pii_guard_db()
    _db = TPRMSessionLocal()
    seed_tprm_database(_db)
    _db.close()
except Exception as e:
    print(f"Database initialization warning: {e}")

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

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".txt",
    ".text",
    ".json",
    ".png",
    ".jpg",
    ".jpeg",
}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
ROOT_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = ROOT_DIR / "demo_samples" / "fixtures"
MANIFEST_PATH = ROOT_DIR / "demo_samples" / "manifest.json"

# In-memory cache for fast lookup during active sessions
_DOC_CACHE: Dict[str, Dict[str, Any]] = {}

# Active authentication tokens
_AUTH_TOKENS: Dict[str, Dict[str, Any]] = {}

# User directory
DEFAULT_PERSONAS = {
    "admin@cadence.com": {
        "id": "usr_lead_auditor",
        "email": "admin@cadence.com",
        "full_name": "Daniela Figueroa",
        "title": "Lead Compliance Auditor & Privacy Officer",
        "role": "ADMIN",
        "permissions": ["read", "write", "redact", "release", "audit", "admin"],
    },
    "analyst@cadence.com": {
        "id": "usr_privacy_analyst",
        "email": "analyst@cadence.com",
        "full_name": "Marcus Vance",
        "title": "Senior Privacy & PII Analyst",
        "role": "ANALYST",
        "permissions": ["read", "write", "redact", "audit"],
    },
    "auditor@cadence.com": {
        "id": "usr_ext_auditor",
        "email": "auditor@cadence.com",
        "full_name": "Sarah Chen",
        "title": "Independent Control Auditor",
        "role": "AUDITOR",
        "permissions": ["read", "audit"],
    },
}


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
    original_ref: Optional[str] = None
    extracted_text: Optional[str]
    redacted_text: Optional[str]
    entities: List[Dict[str, Any]]


class AssistantRequest(BaseModel):
    document_id: str
    query: Optional[str] = None
    topic: Optional[str] = "general"


class FindingReviewRequest(BaseModel):
    status: str  # MASKED, MANUAL_REVIEW, PRESERVED
    notes: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: Optional[str] = None


def get_current_user(x_user_email: Optional[str] = Header(None)) -> Dict[str, Any]:
    email = x_user_email or "admin@cadence.com"
    return DEFAULT_PERSONAS.get(email, DEFAULT_PERSONAS["admin@cadence.com"])


def calculate_integrity_hash(file_bytes: bytes) -> str:
    """Calculate SHA-256 integrity hash of document bytes."""
    return hashlib.sha256(file_bytes).hexdigest()


# ---------------------------------------------------------------------------
# Health & Status
# ---------------------------------------------------------------------------

@app.get("/health")
def root_health_check():
    return {
        "status": "healthy",
        "service": "optiv-document-privacy-workspace",
        "version": "2.0.0",
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "pii-guard-backend",
        "version": "2.0.0",
        "governance": "Cadence Financial Group & Optiv Security",
        "pipeline_stages": [
            "RECEIVED",
            "VALIDATED",
            "EXTRACTED",
            "DETECTED",
            "REDACTED",
            "VERIFIED",
            "RELEASED",
        ],
    }


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Document Processing
# ---------------------------------------------------------------------------

@app.post("/api/process", response_model=ProcessResponse)
async def process_document_endpoint(
    file: Optional[UploadFile] = File(None),
    scenario_filename: Optional[str] = Form(None),
    simulate_verification_failure: bool = Form(False),
):
    """Execute end-to-end PII protection pipeline on uploaded document or scenario fixture."""
    temp_path: Optional[Path] = None
    orig_name = "document.txt"
    file_bytes = b""

    try:
        if scenario_filename:
            safe_name = Path(scenario_filename).name
            fixture_path = FIXTURES_DIR / safe_name
            if not fixture_path.exists():
                raise HTTPException(status_code=404, detail=f"Scenario fixture '{safe_name}' not found.")
            orig_name = safe_name
            file_bytes = fixture_path.read_bytes()

            suffix = fixture_path.suffix.lower()
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                temp_path = Path(tmp.name)
                tmp.write(file_bytes)

        elif file:
            orig_name = file.filename or "document.txt"
            suffix = Path(orig_name).suffix.lower()
            if suffix not in SUPPORTED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file extension '{suffix}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
                )

            file_bytes = await file.read()
            if len(file_bytes) > MAX_FILE_SIZE_BYTES:
                raise HTTPException(status_code=400, detail="File exceeds maximum allowed size of 50 MB.")
            if len(file_bytes) == 0:
                raise HTTPException(status_code=400, detail="Uploaded file is 0 bytes (empty).")

            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                temp_path = Path(tmp.name)
                tmp.write(file_bytes)
        else:
            raise HTTPException(status_code=400, detail="No file or scenario provided.")

        # Compute document hash
        file_hash = calculate_integrity_hash(file_bytes)
        art_mgr = get_default_artifact_manager()

        # Store immutable original separately
        ext_clean = Path(orig_name).suffix.lower().lstrip(".") or "txt"
        mime_map = {
            "pdf": "application/pdf",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "json": "application/json",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "txt": "text/plain",
        }
        orig_content_type = mime_map.get(ext_clean, "application/octet-stream")

        # Run authoritative backend pipeline
        options = {"simulate_verification_failure": simulate_verification_failure}
        res: ProcessingResult = process_document(str(temp_path), options=options)

        # Store original with document_id binding
        orig_ref = art_mgr.store_artifact(
            document_id=res.document_id,
            content=file_bytes,
            file_extension=ext_clean,
            content_type=orig_content_type,
        )

        # Retrieve extracted text and entities for UI inspection
        extracted_text = ""
        entities_data: List[Dict[str, Any]] = []
        try:
            cfg = IngestionConfig.from_env()
            ext_doc = extract_document(str(temp_path), config=cfg)
            extracted_text = ext_doc.text
            det_res = detect_pii(ext_doc)
            for idx, ent in enumerate(det_res.entities):
                val = extracted_text[ent.start:ent.end] if ent.end <= len(extracted_text) else ""
                masked = DEFAULT_POLICY.get(ent.type.upper(), f"[REDACTED_{ent.type}]")
                # Determine page or slide
                page_num = 1
                for p in ext_doc.pages:
                    if p.start <= ent.start < p.end:
                        page_num = p.index
                        break

                entities_data.append({
                    "id": f"fnd-{res.document_id}-{idx + 1}",
                    "type": ent.type,
                    "start": ent.start,
                    "end": ent.end,
                    "confidence": ent.confidence,
                    "value": val,
                    "masked_value": masked,
                    "detector_method": "Deterministic Regex / Validator",
                    "rule_id": f"POL_{ent.type.upper()}",
                    "rationale": f"Identified sensitive {ent.type} entity conforming to Cadence Financial Governance Mandate",
                    "page": page_num,
                })
        except Exception:
            pass

        # Native Format Redaction Generation
        if res.release_allowed and res.verification_status == "PASS":
            try:
                native_ext = Path(orig_name).suffix.lower()
                native_out = temp_path.parent / f"sanitized_{res.document_id}{native_ext}"

                if native_ext == ".pdf":
                    if redact_native_pdf(temp_path, entities_data, native_out) and native_out.exists():
                        res.artifact_ref = art_mgr.store_artifact(
                            document_id=res.document_id,
                            content=native_out.read_bytes(),
                            file_extension="pdf",
                            content_type="application/pdf",
                        )
                elif native_ext == ".pptx":
                    if redact_native_pptx(temp_path, entities_data, native_out) and native_out.exists():
                        res.artifact_ref = art_mgr.store_artifact(
                            document_id=res.document_id,
                            content=native_out.read_bytes(),
                            file_extension="pptx",
                            content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        )
                elif native_ext == ".json":
                    if redact_native_json(temp_path, entities_data, native_out) and native_out.exists():
                        res.artifact_ref = art_mgr.store_artifact(
                            document_id=res.document_id,
                            content=native_out.read_bytes(),
                            file_extension="json",
                            content_type="application/json",
                        )
                elif native_ext in (".png", ".jpg", ".jpeg"):
                    if redact_native_image(temp_path, entities_data, native_out) and native_out.exists():
                        res.artifact_ref = art_mgr.store_artifact(
                            document_id=res.document_id,
                            content=native_out.read_bytes(),
                            file_extension="png",
                            content_type="image/png",
                        )
                if native_out.exists():
                    native_out.unlink()
            except Exception as e:
                print(f"Native redaction packaging notice: {e}")

        # Retrieve redacted text if release is allowed
        redacted_text = None
        if res.release_allowed and res.artifact_ref:
            try:
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
            "original_ref": orig_ref,
            "extracted_text": extracted_text,
            "redacted_text": redacted_text,
            "entities": entities_data,
        }

        # Cache for immediate session
        _DOC_CACHE[res.document_id] = {
            "result": res,
            "payload": response_payload,
            "orig_filename": orig_name,
            "file_type": ext_clean,
            "file_size": len(file_bytes),
            "hash": file_hash,
            "orig_ref": orig_ref,
        }

        # Persistent database storage
        try:
            trail = get_global_audit_trail()
            audit_events = trail.export_sanitized_log(res.document_id)
            with TPRMSessionLocal() as db:
                save_processing_run(
                    db=db,
                    payload=response_payload,
                    entities=entities_data,
                    audit_events=audit_events,
                    original_filename=orig_name,
                    file_type=ext_clean,
                    file_size_bytes=len(file_bytes),
                    integrity_hash=file_hash,
                    original_ref=orig_ref,
                )
        except Exception as ex:
            print(f"Warning: persistence save failed: {ex}")

        return ProcessResponse(**response_payload)

    finally:
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Overview Metrics
# ---------------------------------------------------------------------------

@app.get("/api/overview/metrics")
def get_metrics_endpoint():
    """Retrieve live computed operational indicators from persistent storage."""
    try:
        with TPRMSessionLocal() as db:
            metrics = get_overview_metrics(db)
            return metrics
    except Exception as e:
        return {
            "documents_received": len(_DOC_CACHE),
            "processing_runs_completed": len(_DOC_CACHE),
            "findings_detected": sum(
                len(c["payload"]["entities"]) for c in _DOC_CACHE.values()
            ),
            "findings_successfully_masked": sum(
                c["payload"]["redactions_applied"] for c in _DOC_CACHE.values()
            ),
            "verification_failures": sum(
                1 for c in _DOC_CACHE.values() if c["payload"]["verification_status"] == "FAIL"
            ),
            "documents_awaiting_review": 0,
            "documents_blocked_from_release": sum(
                1 for c in _DOC_CACHE.values() if not c["payload"]["release_allowed"]
            ),
            "documents_approved_for_release": sum(
                1 for c in _DOC_CACHE.values() if c["payload"]["release_allowed"]
            ),
            "category_breakdown": {},
            "recent_activity": [c["payload"] for c in list(_DOC_CACHE.values())[-5:]],
        }


# ---------------------------------------------------------------------------
# Processing Runs
# ---------------------------------------------------------------------------

@app.get("/api/runs")
def list_runs_endpoint(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Retrieve historical and live processing runs."""
    try:
        with TPRMSessionLocal() as db:
            runs = list_processing_runs(db, workflow_status=status, limit=limit, offset=offset)
            return {"runs": [r.to_dict() for r in runs], "total": len(runs)}
    except Exception:
        # Fallback to cache
        cached_runs = [c["payload"] for c in _DOC_CACHE.values()]
        return {"runs": cached_runs, "total": len(cached_runs)}


@app.get("/api/runs/{document_id}")
def get_run_endpoint(document_id: str):
    """Retrieve a single processing run with full stage telemetry."""
    cached = _DOC_CACHE.get(document_id)
    if cached:
        return cached["payload"]

    try:
        with TPRMSessionLocal() as db:
            run = get_processing_run(db, document_id)
            if run:
                return run.to_dict()
    except Exception:
        pass

    raise HTTPException(status_code=404, detail="Processing run not found")


# ---------------------------------------------------------------------------
# Findings & Review
# ---------------------------------------------------------------------------

@app.get("/api/findings")
def list_findings_endpoint(
    document_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Retrieve classified PII findings with filtering."""
    try:
        with TPRMSessionLocal() as db:
            findings = list_findings(
                db, document_id=document_id, category=category, status=status, limit=limit, offset=offset
            )
            return {"findings": [f.to_dict() for f in findings], "total": len(findings)}
    except Exception:
        # Fallback
        res_list = []
        for c in _DOC_CACHE.values():
            if document_id and c["result"].document_id != document_id:
                continue
            for ent in c["payload"]["entities"]:
                if category and category.upper() != "ALL" and ent["type"].upper() != category.upper():
                    continue
                res_list.append(ent)
        return {"findings": res_list, "total": len(res_list)}


@app.post("/api/findings/{finding_id}/review")
def review_finding_endpoint(finding_id: str, req: FindingReviewRequest):
    """Apply manual reviewer action to a finding."""
    try:
        with TPRMSessionLocal() as db:
            f = update_finding_status(db, finding_id, req.status, req.notes)
            if not f:
                raise HTTPException(status_code=404, detail="Finding not found")
            return {"status": "success", "finding": f.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Downloads & Exports
# ---------------------------------------------------------------------------

@app.get("/api/original/{document_id}")
def download_original_document(
    document_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """Download the immutable original document (permission-governed)."""
    if "admin" not in user.get("permissions", []) and "release" not in user.get("permissions", []):
        raise HTTPException(
            status_code=403,
            detail="Access denied: Original document retrieval requires Compliance Officer authorization.",
        )

    cached = _DOC_CACHE.get(document_id)
    art_mgr = get_default_artifact_manager()

    orig_ref = cached.get("orig_ref") if cached else None
    orig_name = cached.get("orig_filename", "original_document") if cached else "original_document"

    if not orig_ref:
        try:
            with TPRMSessionLocal() as db:
                run = get_processing_run(db, document_id)
                if run and run.original_ref:
                    orig_ref = run.original_ref
                    orig_name = run.original_filename
        except Exception:
            pass

    if not orig_ref:
        raise HTTPException(status_code=404, detail="Original document artifact not found.")

    try:
        data = art_mgr.read_artifact_bytes(orig_ref, document_id, True)
        ext = Path(orig_name).suffix.lstrip(".") or "bin"
        mime_map = {
            "pdf": "application/pdf",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "json": "application/json",
            "png": "image/png",
            "jpg": "image/jpeg",
            "txt": "text/plain",
        }
        return Response(
            content=data,
            media_type=mime_map.get(ext, "application/octet-stream"),
            headers={"Content-Disposition": f'attachment; filename="original_{Path(orig_name).name}"'},
        )
    except Exception as ex:
        raise HTTPException(status_code=500, detail=sanitize_error_message(str(ex)))


@app.get("/api/artifact/{document_id}")
def download_artifact(document_id: str):
    """Controlled artifact download endpoint with strict fail-closed release gate enforcement."""
    cached = _DOC_CACHE.get(document_id)
    res = cached.get("result") if cached else None
    orig_name = cached.get("orig_filename", "document") if cached else "document"

    if not res:
        try:
            with TPRMSessionLocal() as db:
                run = get_processing_run(db, document_id)
                if run:
                    if not run.release_allowed or run.verification_status != "PASS" or not run.artifact_ref:
                        raise HTTPException(
                            status_code=403,
                            detail="Release gate BLOCKED: Document failed independent verification or release is unauthorized.",
                        )
                    art_mgr = get_default_artifact_manager()
                    data = art_mgr.read_artifact_bytes(run.artifact_ref, run.document_id, True)
                    ext = run.file_type or "txt"
                    clean_name = f"sanitized_{Path(run.original_filename).stem}.{ext}"
                    return Response(
                        content=data,
                        media_type="text/plain" if ext == "txt" else "application/octet-stream",
                        headers={"Content-Disposition": f'attachment; filename="{clean_name}"'},
                    )
        except HTTPException:
            raise
        except Exception:
            pass
        raise HTTPException(status_code=404, detail="Document not found or session expired.")

    if not res.release_allowed or res.verification_status != "PASS" or not res.artifact_ref:
        raise HTTPException(
            status_code=403,
            detail="Release gate BLOCKED: Document failed independent verification or release is unauthorized.",
        )

    art_mgr = get_default_artifact_manager()
    try:
        data = art_mgr.read_artifact_bytes(res.artifact_ref, res.document_id, res.release_allowed)
        ext = res.source_type if res.source_type in ("txt", "docx", "pdf", "pptx", "json", "png") else "txt"
        clean_name = f"sanitized_{Path(orig_name).stem}.{ext}"
        mime_map = {
            "pdf": "application/pdf",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "json": "application/json",
            "png": "image/png",
            "txt": "text/plain",
        }
        return Response(
            content=data,
            media_type=mime_map.get(ext, "application/octet-stream"),
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
    """Retrieve immutable, metadata-only sanitized audit trail for document."""
    trail = get_global_audit_trail()
    events = trail.export_sanitized_log(document_id)
    return {"document_id": document_id, "events": events}


@app.get("/api/audit")
def list_global_audit_endpoint(
    document_id: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Retrieve all audit events across all processing runs."""
    try:
        with TPRMSessionLocal() as db:
            records = list_audit_records(db, document_id=document_id, stage=stage, limit=limit, offset=offset)
            return {"events": [r.to_dict() for r in records], "total": len(records)}
    except Exception:
        trail = get_global_audit_trail()
        return {"events": [e.to_safe_dict() for e in trail._events], "total": len(trail._events)}


# ---------------------------------------------------------------------------
# AI Explanation Agent
# ---------------------------------------------------------------------------

@app.post("/api/assistant/chat")
def assistant_chat(req: AssistantRequest):
    """AI explanation agent explaining technical decisions, verification, and architecture."""
    cached = _DOC_CACHE.get(req.document_id)
    payload = None
    res = None

    if cached:
        payload = cached["payload"]
        res = cached["result"]
    else:
        try:
            with TPRMSessionLocal() as db:
                run = get_processing_run(db, req.document_id)
                if run:
                    payload = run.to_dict()
        except Exception:
            pass

    if not payload:
        raise HTTPException(status_code=404, detail="Document not found.")

    query = (req.query or "").strip().lower()
    topic = req.topic or "general"

    is_released = payload.get("release_allowed", False) and payload.get("verification_status") == "PASS"
    cat_counts = payload.get("category_counts", {})
    total_ents = sum(cat_counts.values())

    explanation = ""
    citations = []

    if "decision" in query or topic == "decision" or ("why" in query and "block" in query) or ("why" in query and "release" in query):
        if is_released:
            explanation = (
                f"### ✅ Release Gate Authorization: GRANTED\n\n"
                f"- **Dual-Key Barrier Assessment:** The pipeline evaluated two strict prerequisites: (1) Independent verification status is `PASS`, and (2) release authorization flag is `True`.\n"
                f"- **Residual PII Re-scan:** The independent verification engine re-examined the generated artifact text and found **0 residual leaks** across all regex, structural, and known-entity checks.\n"
                f"- **Entity Masking:** All {total_ents} detected sensitive entities were masked using contextual tokens (`[REDACTED_<CATEGORY>]`).\n"
                f"- **Download Status:** Client download is authorized under Cadence Financial Group AI Governance Policy."
            )
        else:
            reason = payload.get("safe_error") or "Verification failed or incomplete"
            explanation = (
                f"### 🛑 Release Gate Authorization: BLOCKED\n\n"
                f"- **Fail-Closed Gate Triggered:** The document was withheld because `verification_status` returned `{payload.get('verification_status')}`.\n"
                f"- **Root Cause:** {reason}.\n"
                f"- **Security Invariant:** Under the Zero-Leakage Mandate, unredacted or unverified document egress to downstream LLMs is prohibited.\n"
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
            f"  - **Deterministic Pattern Matchers:** Validated patterns with checksum algorithms (Luhn for Credit Cards, area/group checks for SSN, holder-type codes for Indian PAN).\n"
            f"  - **Precedence Resolution:** Spans are sorted by precedence (Government ID / Cards > Email / Employee ID > IP > Phone > Person).\n"
            f"  - **Boundary Safety:** Zero spans cross document form-feed markers."
        )
        citations = ["src/pii_guard/detection/pattern_detector.py", "src/pii_guard/detection/classifier.py"]

    elif "leak" in query or "verification" in query or topic == "leakage":
        explanation = (
            f"### 🔍 Independent Verification & Secondary Re-scan\n\n"
            f"- **Independent Verification Plane:** Redaction verification does not rely on the detection engine. It executes an autonomous secondary scanner across the saved artifact.\n"
            f"- **Checks Performed:**\n"
            f"  1. **Known Value Matching:** Verifies that no original unmasked values from the detection stage remain in the output.\n"
            f"  2. **Residual Pattern Scanning:** Runs independent regex passes for phone numbers, email addresses, government IDs, Luhn-valid cards, and IP addresses.\n"
            f"  3. **Structure Retention Scoring:** Validates that layout, line breaks, and paragraph boundaries were preserved (Score >= 80%).\n"
            f"- **Current Verification Status:** `{payload.get('verification_status')}`"
        )
        citations = ["src/pii_guard/redaction/verifier.py", "src/pii_guard/redaction/service.py"]

    elif "audit" in query or "policy" in query or topic == "policy":
        explanation = (
            f"### 📜 Cadence Financial Zero-Leakage Audit Policy\n\n"
            f"- **Immutable Audit Trail:** All pipeline lifecycle transitions (`RECEIVED` through `RELEASED`) are atomically logged.\n"
            f"- **Metadata-Only Projection:** Strict allowlist serialization guarantees that **zero raw document text** and **zero detected PII values** are written to audit records or JSON exports.\n"
            f"- **Cryptographic Isolation:** Protected artifacts are isolated in temporary sandbox storage addressed by opaque UUID tokens (`art-<uuid>`), preventing path traversal."
        )
        citations = ["src/pii_guard/reporting/audit.py", "src/pii_guard/orchestration/artifacts.py"]

    else:
        status_banner = "✅ Authorized for Downstream LLMs" if is_released else "🛑 Blocked / Withheld"
        explanation = (
            f"### 🛡️ PII Guard Executive Assistant Summary\n\n"
            f"- **Document ID:** `{payload.get('document_id')}`\n"
            f"- **Outcome:** **{status_banner}** (Workflow: `{payload.get('workflow_status', 'UNKNOWN').upper()}`)\n"
            f"- **Format & Scale:** `{payload.get('source_type') or 'unknown'}` format | {payload.get('pages_count')} pages | {payload.get('char_count')} characters\n"
            f"- **Entities Masked:** {payload.get('redactions_applied')} PII spans across {len(cat_counts)} categories\n"
            f"- **Verification Gate:** Status `{payload.get('verification_status')}` | Release Allowed: `{payload.get('release_allowed')}`\n"
            f"- **Processing Duration:** {payload.get('duration_sec')} seconds across all execution stages.\n\n"
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


# ---------------------------------------------------------------------------
# Authentication & IAM
# ---------------------------------------------------------------------------

@app.post("/api/auth/login")
def login_endpoint(req: LoginRequest):
    """Authenticate user persona and return profile."""
    user = DEFAULT_PERSONAS.get(req.email)
    if not user:
        # Default fallback persona
        user = {
            "id": f"usr_{hashlib.md5(req.email.encode()).hexdigest()[:8]}",
            "email": req.email,
            "full_name": req.email.split("@")[0].replace(".", " ").title(),
            "title": "Privacy Compliance Specialist",
            "role": "ANALYST",
            "permissions": ["read", "write", "redact", "audit"],
        }
    token = f"tok_{hashlib.sha256(f'{req.email}_{datetime.now().isoformat()}'.encode()).hexdigest()[:24]}"
    _AUTH_TOKENS[token] = user
    return {"token": token, "user": user}


@app.get("/api/auth/me")
def get_me_endpoint(user: Dict[str, Any] = Depends(get_current_user)):
    """Return active authenticated user profile."""
    return {"user": user}


@app.post("/api/auth/logout")
def logout_endpoint():
    """Clear session token."""
    return {"status": "logged_out"}


# ---------------------------------------------------------------------------
# System Settings & Governance Policy Configuration
# ---------------------------------------------------------------------------

_SYSTEM_SETTINGS = {
    "zero_leakage_mandate": True,
    "minimum_structure_score": 0.80,
    "confidence_threshold": 0.50,
    "ocr_confidence_threshold": 60.0,
    "enforce_luhn_check": True,
    "ai_explanation_mode": "DETERMINISTIC_EVIDENCE_GROUNDED",
    "retention_policy_days": 30,
    "supported_formats": sorted(list(SUPPORTED_EXTENSIONS)),
}


@app.get("/api/settings")
def get_settings_endpoint():
    return _SYSTEM_SETTINGS


@app.post("/api/settings")
def update_settings_endpoint(updates: Dict[str, Any]):
    _SYSTEM_SETTINGS.update(updates)
    return {"status": "updated", "settings": _SYSTEM_SETTINGS}


# ---------------------------------------------------------------------------
# Static Frontend Serving
# ---------------------------------------------------------------------------

FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
