"""Central pipeline orchestration coordinator (Member 5 - Tirth).

Coordinates the multi-stage document lifecycle:
RECEIVED -> VALIDATED -> EXTRACTED -> DETECTED -> REDACTED -> VERIFIED -> RELEASED (or BLOCKED/FAILED)

FAIL-CLOSED RELEASE GATE:
A document is released ONLY if verification_status is PASS AND release_allowed is True.
Under all other conditions, artifact release is strictly blocked.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, Callable, TYPE_CHECKING

from .state import PipelineStage, PipelineStateManager
from .errors import sanitize_error_message
from .models import (
    ProcessingResult,
    DetectionResult,
    RedactionResult,
)
from .artifacts import ArtifactManager, get_default_artifact_manager
from ..ingestion.extractor import extract_document
from ..ingestion.config import IngestionConfig

if TYPE_CHECKING:
    from ..reporting.audit import AuditTrail


def process_document(
    file_path: str,
    options: Optional[Dict[str, Any]] = None,
    detector_fn: Optional[Callable] = None,
    redactor_fn: Optional[Callable] = None,
    audit_trail: Optional[AuditTrail] = None,
    artifact_manager: Optional[ArtifactManager] = None,
) -> ProcessingResult:
    """Execute end-to-end PII protection pipeline.
    
    GUARANTEES:
    1. Zero unhandled exceptions leaked to caller; fail-closed under all failure modes.
    2. Zero document text or PII leaked in public ProcessingResult or error messages.
    3. Document release strictly requires verification_status == PASS and release_allowed == True.
    """
    options = options or {}
    start_time = datetime.now(timezone.utc)
    doc_id = f"doc-{uuid.uuid4().hex[:12]}"
    if audit_trail is None:
        from ..reporting.audit import get_global_audit_trail
        trail = get_global_audit_trail()
    else:
        trail = audit_trail
    art_mgr = artifact_manager or get_default_artifact_manager()

    state_mgr = PipelineStateManager()

    try:
        # -------------------------------------------------------------------
        # 1. STAGE: RECEIVED
        # -------------------------------------------------------------------
        state_mgr.transition_to(
            PipelineStage.RECEIVED,
            message="Document received by pipeline coordinator",
            metadata={"file_suffix": Path(file_path).suffix.lower()},
        )
        trail.record_event(
            document_id=doc_id,
            stage=PipelineStage.RECEIVED,
            event_type="DOCUMENT_RECEIVED",
            status="success",
        )

        p = Path(file_path)
        if not p.is_file():
            state_mgr.transition_to_failed(
                message="Target document path does not exist or is not a file",
                safe_code="ERR_FILE_NOT_FOUND",
            )
            trail.record_event(
                document_id=doc_id,
                stage=PipelineStage.FAILED,
                event_type="VALIDATION_FAILED",
                status="failure",
                error_code="ERR_FILE_NOT_FOUND",
            )
            return ProcessingResult(
                document_id=doc_id,
                workflow_status="failed",
                current_stage=PipelineStage.FAILED,
                stage_history=state_mgr.history,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                safe_error="Specified document file could not be found",
                safe_error_code="ERR_FILE_NOT_FOUND",
            )

        # -------------------------------------------------------------------
        # 2. STAGE: VALIDATED
        # -------------------------------------------------------------------
        state_mgr.transition_to(PipelineStage.VALIDATED, message="Pre-flight validation starting")
        trail.record_event(
            document_id=doc_id,
            stage=PipelineStage.VALIDATED,
            event_type="STAGE_ENTER",
            status="success",
        )

        # -------------------------------------------------------------------
        # 3. STAGE: EXTRACTED
        # -------------------------------------------------------------------
        state_mgr.transition_to(PipelineStage.EXTRACTED, message="Calling ingestion extractor")
        t_ext_start = time.perf_counter()

        ingest_cfg = IngestionConfig.from_env()
        extracted_doc = extract_document(str(p), config=ingest_cfg)
        t_ext_sec = time.perf_counter() - t_ext_start
        initial_doc_id = doc_id
        doc_id = extracted_doc.document_id
        trail.relink_document_id(initial_doc_id, doc_id)

        # Propagate warnings safely
        safe_warn_codes = [w.code for w in extracted_doc.warnings]

        if extracted_doc.extraction_status == "failed":
            first_err_code = safe_warn_codes[0] if safe_warn_codes else "ERR_EXTRACTION_FAILED"
            state_mgr.transition_to_failed(
                message="Document ingestion extraction failed",
                safe_code=first_err_code,
            )
            trail.record_event(
                document_id=doc_id,
                stage=PipelineStage.FAILED,
                event_type="EXTRACTION_FAILED",
                status="failure",
                duration_sec=t_ext_sec,
                error_code=first_err_code,
            )
            return ProcessingResult(
                document_id=doc_id,
                workflow_status="failed",
                current_stage=PipelineStage.FAILED,
                stage_history=state_mgr.history,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                source_type=extracted_doc.source_type,
                pages_count=len(extracted_doc.pages),
                char_count=len(extracted_doc.text),
                extraction_status="failed",
                safe_warnings=safe_warn_codes,
                safe_error="Document extraction could not extract valid text",
                safe_error_code=first_err_code,
            )

        trail.record_event(
            document_id=doc_id,
            stage=PipelineStage.EXTRACTED,
            event_type="STAGE_EXIT",
            status=extracted_doc.extraction_status,
            duration_sec=t_ext_sec,
        )

        # Partial extraction is not safe for automatic release. Detection can
        # still be useful for diagnostics, but the authoritative pipeline must
        # stop before redaction/release because unseen source content may
        # contain undetected PII.
        if extracted_doc.extraction_status == "partial":
            partial_code = "WARN_PARTIAL_EXTRACTION_REQUIRES_REVIEW"
            safe_warn_codes.append(partial_code)
            state_mgr.transition_to(
                PipelineStage.INCOMPLETE,
                message="Partial extraction detected; manual review required before release",
                metadata={"error_code": partial_code},
            )
            trail.record_event(
                document_id=doc_id,
                stage=PipelineStage.INCOMPLETE,
                event_type="PARTIAL_EXTRACTION_BLOCKED",
                status="incomplete",
                duration_sec=t_ext_sec,
                error_code=partial_code,
            )
            return ProcessingResult(
                document_id=doc_id,
                workflow_status="incomplete",
                current_stage=PipelineStage.INCOMPLETE,
                stage_history=state_mgr.history,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                source_type=extracted_doc.source_type,
                pages_count=len(extracted_doc.pages),
                char_count=len(extracted_doc.text),
                extraction_status="partial",
                safe_warnings=safe_warn_codes,
                safe_error="Document extraction was incomplete; release requires manual review",
                safe_error_code=partial_code,
                release_allowed=False,
                artifact_ref=None,
            )

        # -------------------------------------------------------------------
        # 4. STAGE: DETECTED
        # -------------------------------------------------------------------
        state_mgr.transition_to(PipelineStage.DETECTED, message="Initiating PII detection")
        t_det_start = time.perf_counter()

        if detector_fn is not None:
            detection_res = detector_fn(extracted_doc)
        else:
            from ..detection.detector import detect_pii
            from ..detection.ner_detector import get_default_ner_backend
            detection_res = detect_pii(extracted_doc, ner_backend=get_default_ner_backend())


        t_det_sec = time.perf_counter() - t_det_start

        # Aggregate counts by category
        category_counts: Dict[str, int] = {}
        for ent in detection_res.entities:
            c = ent.type.upper()
            category_counts[c] = category_counts.get(c, 0) + 1

        trail.record_event(
            document_id=doc_id,
            stage=PipelineStage.DETECTED,
            event_type="STAGE_EXIT",
            status="success",
            duration_sec=t_det_sec,
            entity_count=len(detection_res.entities),
            category_counts=category_counts,
        )

        # -------------------------------------------------------------------
        # 5. STAGE: REDACTED
        # -------------------------------------------------------------------
        state_mgr.transition_to(PipelineStage.REDACTED, message="Applying entity masking")
        t_red_start = time.perf_counter()

        sim_fail = options.get("simulate_verification_failure", False)
        if redactor_fn is not None:
            redaction_res = redactor_fn(extracted_doc, detection_res)
        else:
            from ..redaction.redactor import redact_and_validate
            redaction_res = redact_and_validate(
                extracted_doc,
                detection_res,
                artifact_manager=art_mgr,
                simulate_verification_failure=sim_fail,
            )

        t_red_sec = time.perf_counter() - t_red_start
        trail.record_event(
            document_id=doc_id,
            stage=PipelineStage.REDACTED,
            event_type="STAGE_EXIT",
            status="success",
            duration_sec=t_red_sec,
            entity_count=redaction_res.redactions_applied,
        )

        # -------------------------------------------------------------------
        # 6. STAGE: VERIFIED
        # -------------------------------------------------------------------
        state_mgr.transition_to(
            PipelineStage.VERIFIED,
            message="Evaluating independent post-redaction verification",
            metadata={"verification_status": redaction_res.verification_status},
        )
        trail.record_event(
            document_id=doc_id,
            stage=PipelineStage.VERIFIED,
            event_type="VERIFICATION_EVALUATED",
            status="success",
            verification_status=redaction_res.verification_status,
            release_decision=redaction_res.release_allowed,
        )

        # -------------------------------------------------------------------
        # 7. RELEASE GATE AUTHORIZATION DECISION (FAIL-CLOSED)
        # -------------------------------------------------------------------
        is_pass = (redaction_res.verification_status == "PASS")
        is_release_authorized = bool(redaction_res.release_allowed and is_pass)

        if is_release_authorized:
            state_mgr.transition_to(
                PipelineStage.RELEASED,
                message="Release gate passed: document authorized for client download",
            )
            workflow_status = "success"
            effective_artifact_ref = redaction_res.artifact_ref
            safe_err = None
            safe_err_code = None
        elif redaction_res.verification_status == "FAIL":
            state_mgr.transition_to_blocked(
                message="Release gate BLOCKED: residual PII or verification failure detected"
            )
            workflow_status = "blocked"
            effective_artifact_ref = None  # Withhold artifact token
            safe_err = "Verification re-scan detected residual PII: release is blocked"
            safe_err_code = "WARN_RELEASE_BLOCKED"
        else:
            # INCOMPLETE or unrecognized
            state_mgr.transition_to(
                PipelineStage.INCOMPLETE,
                message="Release gate INCOMPLETE: verification check was interrupted",
            )
            workflow_status = "incomplete"
            effective_artifact_ref = None
            safe_err = "Verification re-scan could not be completed: release is withheld"
            safe_err_code = "WARN_VERIFICATION_INCOMPLETE"

        finish_time = datetime.now(timezone.utc)

        result = ProcessingResult(
            document_id=doc_id,
            workflow_status=workflow_status,
            current_stage=state_mgr.current_stage,
            stage_history=state_mgr.history,
            started_at=start_time,
            completed_at=finish_time,
            source_type=extracted_doc.source_type,
            pages_count=len(extracted_doc.pages),
            char_count=len(extracted_doc.text),
            extraction_status=extracted_doc.extraction_status,
            detection_status="success",
            redaction_status="success",
            verification_status=redaction_res.verification_status,
            release_allowed=is_release_authorized,
            category_counts=category_counts,
            redactions_applied=redaction_res.redactions_applied,
            safe_warnings=safe_warn_codes,
            safe_error=safe_err,
            safe_error_code=safe_err_code,
            artifact_ref=effective_artifact_ref,
        )

        # Generate report and audit references
        from ..reporting.report_generator import generate_report
        report = generate_report(result)
        result.report_id = f"rep-{doc_id}"
        result.audit_id = f"aud-{doc_id}"

        trail.record_event(
            document_id=doc_id,
            stage=state_mgr.current_stage,
            event_type="RELEASE_DECIDED",
            status=workflow_status,
            verification_status=redaction_res.verification_status,
            release_decision=is_release_authorized,
            report_ref=result.report_id,
        )

        return result

    except Exception as e:
        # Fail-closed top-level safeguard: NEVER expose unhandled exceptions or paths
        finish_time = datetime.now(timezone.utc)
        safe_msg = sanitize_error_message(str(e))
        try:
            state_mgr.transition_to_failed(message=safe_msg)
        except Exception:
            pass

        trail.record_event(
            document_id=doc_id,
            stage=PipelineStage.FAILED,
            event_type="INTERNAL_EXCEPTION",
            status="failure",
            error_code="ERR_INTERNAL_PIPELINE_FAULT",
            message=safe_msg,
        )

        return ProcessingResult(
            document_id=doc_id,
            workflow_status="failed",
            current_stage=PipelineStage.FAILED,
            stage_history=state_mgr.history,
            started_at=start_time,
            completed_at=finish_time,
            safe_error="An internal error occurred during pipeline execution",
            safe_error_code="ERR_INTERNAL_PIPELINE_FAULT",
            release_allowed=False,
            artifact_ref=None,
        )
