"""Repository layer providing clean CRUD and metric computation for PII Guard records."""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from src.cadence_tprm.database import SessionLocal, engine, Base
from .models import PIIProcessingRun, PIIFinding, PIIAuditRecord


def init_pii_guard_db():
    """Ensure PII Guard tables exist in database schema."""
    Base.metadata.create_all(bind=engine)


def save_processing_run(
    db: Session,
    payload: Dict[str, Any],
    entities: List[Dict[str, Any]],
    audit_events: List[Dict[str, Any]],
    original_filename: str,
    file_type: str,
    file_size_bytes: int,
    integrity_hash: Optional[str] = None,
    original_ref: Optional[str] = None,
) -> PIIProcessingRun:
    """Atomically persist or update a complete processing run with findings and audit logs."""
    doc_id = payload["document_id"]

    run = db.query(PIIProcessingRun).filter_by(document_id=doc_id).first()
    if not run:
        run = PIIProcessingRun(
            document_id=doc_id,
            original_filename=original_filename,
            file_type=file_type,
            file_size_bytes=file_size_bytes,
            integrity_hash=integrity_hash,
            original_ref=original_ref,
        )
        db.add(run)

    run.workflow_status = payload.get("workflow_status", "pending")
    run.current_stage = payload.get("current_stage", "RECEIVED")
    run.duration_sec = payload.get("duration_sec", 0.0)
    run.pages_count = payload.get("pages_count", 1)
    run.char_count = payload.get("char_count", 0)
    run.extraction_status = payload.get("extraction_status", "pending")
    run.detection_status = payload.get("detection_status", "pending")
    run.redaction_status = payload.get("redaction_status", "pending")
    run.verification_status = payload.get("verification_status", "pending")
    run.release_allowed = payload.get("release_allowed", False)
    run.category_counts_json = json.dumps(payload.get("category_counts", {}))
    run.redactions_applied = payload.get("redactions_applied", 0)
    run.safe_warnings_json = json.dumps(payload.get("safe_warnings", []))
    run.safe_error = payload.get("safe_error")
    run.safe_error_code = payload.get("safe_error_code")
    run.artifact_ref = payload.get("artifact_ref")
    run.extracted_text = payload.get("extracted_text")
    run.redacted_text = payload.get("redacted_text")
    run.stage_history_json = json.dumps(payload.get("stage_history", []))
    run.completed_at = datetime.now(timezone.utc)

    # Replace findings
    db.query(PIIFinding).filter_by(document_id=doc_id).delete()
    for idx, ent in enumerate(entities):
        f_id = f"fnd-{doc_id}-{idx + 1}"
        finding = PIIFinding(
            id=f_id,
            document_id=doc_id,
            finding_index=idx + 1,
            entity_type=ent.get("type", "UNKNOWN").upper(),
            start_offset=ent.get("start", 0),
            end_offset=ent.get("end", 0),
            confidence=float(ent.get("confidence", 1.0)),
            value_masked=ent.get("value", ""),
            replacement_mask=ent.get("masked_value", ""),
            detector_method=ent.get("detector_method", "pattern_matcher"),
            rule_id=ent.get("rule_id", f"RULE_{ent.get('type', 'PII').upper()}"),
            rationale=ent.get("rationale") or f"Matched sensitive pattern for category {ent.get('type')}",
            status="MASKED" if run.release_allowed else "FLAGGED",
            verification_result="VERIFIED_REMOVED" if run.verification_status == "PASS" else "FAIL",
            page_or_slide=ent.get("page", 1),
            risk_level="CRITICAL" if ent.get("type") in ("GOVERNMENT_ID", "FINANCIAL_IDENTIFIER") else "HIGH",
        )
        db.add(finding)

    # Save audit events
    existing_evt_ids = {r.event_id for r in db.query(PIIAuditRecord.event_id).filter_by(document_id=doc_id).all()}
    for evt in audit_events:
        e_id = evt.get("event_id") or f"evt-{uuid.uuid4().hex[:12]}"
        if e_id not in existing_evt_ids:
            audit_rec = PIIAuditRecord(
                id=f"rec-{uuid.uuid4().hex[:12]}",
                event_id=e_id,
                document_id=doc_id,
                stage=evt.get("stage", "STAGE"),
                event_type=evt.get("event_type", "INFO"),
                status=evt.get("status", "success"),
                error_code=evt.get("error_code"),
                duration_sec=evt.get("duration_sec"),
                entity_count=evt.get("entity_count"),
                category_counts_json=json.dumps(evt.get("category_counts", {})),
                verification_status=evt.get("verification_status"),
                release_decision=evt.get("release_decision", False),
                report_ref=evt.get("report_ref"),
                safe_message=evt.get("safe_message"),
                actor=evt.get("actor", "SYSTEM_PII_GUARD"),
            )
            db.add(audit_rec)

    db.commit()
    db.refresh(run)
    return run


def get_processing_run(db: Session, document_id: str) -> Optional[PIIProcessingRun]:
    """Retrieve processing run by document ID."""
    return db.query(PIIProcessingRun).filter_by(document_id=document_id).first()


def list_processing_runs(
    db: Session,
    workflow_status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[PIIProcessingRun]:
    """Retrieve list of processing runs sorted by start time descending."""
    q = db.query(PIIProcessingRun)
    if workflow_status and workflow_status.lower() != "all":
        q = q.filter(PIIProcessingRun.workflow_status == workflow_status.lower())
    return q.order_by(desc(PIIProcessingRun.started_at)).offset(offset).limit(limit).all()


def list_findings(
    db: Session,
    document_id: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[PIIFinding]:
    """Query findings with category and status filters."""
    q = db.query(PIIFinding)
    if document_id:
        q = q.filter(PIIFinding.document_id == document_id)
    if category and category.upper() != "ALL":
        q = q.filter(PIIFinding.entity_type == category.upper())
    if status and status.upper() != "ALL":
        q = q.filter(PIIFinding.status == status.upper())
    return q.order_by(PIIFinding.document_id, PIIFinding.finding_index).offset(offset).limit(limit).all()


def update_finding_status(
    db: Session, finding_id: str, new_status: str, notes: Optional[str] = None
) -> Optional[PIIFinding]:
    """Update review status on finding (e.g. MASKED, MANUAL_REVIEW, PRESERVED)."""
    f = db.query(PIIFinding).filter_by(id=finding_id).first()
    if f:
        f.status = new_status
        if notes:
            f.rationale = f"{f.rationale or ''} [Reviewer note: {notes}]"
        db.commit()
        db.refresh(f)
    return f


def list_audit_records(
    db: Session,
    document_id: Optional[str] = None,
    stage: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[PIIAuditRecord]:
    """Query audit records ordered chronologically."""
    q = db.query(PIIAuditRecord)
    if document_id:
        q = q.filter(PIIAuditRecord.document_id == document_id)
    if stage and stage.upper() != "ALL":
        q = q.filter(PIIAuditRecord.stage == stage.upper())
    return q.order_by(desc(PIIAuditRecord.timestamp)).offset(offset).limit(limit).all()


def get_overview_metrics(db: Session) -> Dict[str, Any]:
    """Compute live, non-hardcoded operational indicators from database."""
    total_runs = db.query(func.count(PIIProcessingRun.document_id)).scalar() or 0
    total_findings = db.query(func.count(PIIFinding.id)).scalar() or 0
    total_masked = db.query(func.count(PIIFinding.id)).filter(PIIFinding.status == "MASKED").scalar() or 0
    verification_failures = db.query(func.count(PIIProcessingRun.document_id)).filter(
        PIIProcessingRun.verification_status == "FAIL"
    ).scalar() or 0
    blocked_runs = db.query(func.count(PIIProcessingRun.document_id)).filter(
        PIIProcessingRun.workflow_status == "blocked"
    ).scalar() or 0
    approved_runs = db.query(func.count(PIIProcessingRun.document_id)).filter(
        PIIProcessingRun.release_allowed == True
    ).scalar() or 0
    review_required = db.query(func.count(PIIFinding.id)).filter(
        PIIFinding.status == "MANUAL_REVIEW"
    ).scalar() or 0

    # Category breakdown
    cat_rows = db.query(PIIFinding.entity_type, func.count(PIIFinding.id)).group_by(PIIFinding.entity_type).all()
    category_counts = {cat: count for cat, count in cat_rows}

    # Recent runs
    recent = db.query(PIIProcessingRun).order_by(desc(PIIProcessingRun.started_at)).limit(5).all()

    return {
        "documents_received": total_runs,
        "processing_runs_completed": total_runs,
        "findings_detected": total_findings,
        "findings_successfully_masked": total_masked,
        "verification_failures": verification_failures,
        "documents_awaiting_review": review_required,
        "documents_blocked_from_release": blocked_runs,
        "documents_approved_for_release": approved_runs,
        "category_breakdown": category_counts,
        "recent_activity": [r.to_dict() for r in recent],
    }
