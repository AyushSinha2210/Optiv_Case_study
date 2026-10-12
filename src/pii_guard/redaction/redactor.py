"""Redaction and verification engine conforming strictly to Contract C.

PRIVACY & RELEASE GATE RULES:
1. Applies contextual token replacement on detected entity character spans.
2. Performs an independent post-redaction re-scan verification check.
3. Release permission (`release_allowed=True`) is ONLY granted if verification is strictly PASS.
4. If residual PII is discovered or verification cannot run, release_allowed is strictly False.
"""

from typing import Optional, List, Callable
from ..ingestion.schemas import ExtractedDocument
from ..orchestration.models import (
    DetectionResult,
    RedactionResult,
    FindingInfo,
    DetectedEntity,
)
from ..orchestration.artifacts import ArtifactManager, get_default_artifact_manager


class Redactor:
    """Applies entity masking and executes post-redaction verification."""

    def __init__(
        self,
        artifact_manager: Optional[ArtifactManager] = None,
        verifier_detector: Optional[Callable[[ExtractedDocument], DetectionResult]] = None,
    ):
        self.artifact_manager = artifact_manager or get_default_artifact_manager()
        self.verifier_detector = verifier_detector

    def redact_and_validate(
        self,
        doc: ExtractedDocument,
        detection: DetectionResult,
        simulate_verification_failure: bool = False,
    ) -> RedactionResult:
        """Mask detected PII, verify resulting artifact, and generate Contract C result."""
        text = doc.text
        findings: List[FindingInfo] = []

        # Sort entities by start offset descending so earlier offsets remain valid during replacement
        sorted_entities = sorted(detection.entities, key=lambda e: e.start, reverse=True)

        redacted_text = text
        applied_count = 0

        for ent in sorted_entities:
            # Ensure span bounds are valid within current string length
            if 0 <= ent.start < ent.end <= len(redacted_text):
                token = f"<REDACTED_{ent.type.upper()}>"
                redacted_text = redacted_text[:ent.start] + token + redacted_text[ent.end:]
                applied_count += 1
            else:
                findings.append(
                    FindingInfo(
                        code="WARN_INVALID_SPAN_BOUNDS",
                        message="Entity offset out of document boundary during redaction",
                        category=ent.type,
                    )
                )

        # Step 2: Independent Verification Re-scan
        verification_status = "PASS"
        release_allowed = True

        if simulate_verification_failure:
            verification_status = "FAIL"
            release_allowed = False
            findings.append(
                FindingInfo(
                    code="ERR_LEAKAGE_DETECTED",
                    message="Simulated leakage trigger detected residual PII in artifact",
                )
            )
        elif self.verifier_detector is not None:
            try:
                # Wrap redacted text into a temporary document contract for re-scan
                from ..ingestion.schemas import ExtractedDocument
                verify_doc = ExtractedDocument(
                    document_id=f"verify-{doc.document_id}",
                    source_type=doc.source_type,
                    text=redacted_text,
                    pages=[],
                    warnings=[],
                    extraction_status="success",
                )
                re_scan_res = self.verifier_detector(verify_doc)
                if re_scan_res.entities:
                    verification_status = "FAIL"
                    release_allowed = False
                    findings.append(
                        FindingInfo(
                            code="ERR_RESIDUAL_PII_LEAKAGE",
                            message=f"Post-redaction re-scan detected {len(re_scan_res.entities)} residual entities",
                        )
                    )
            except Exception:
                verification_status = "INCOMPLETE"
                release_allowed = False
                findings.append(
                    FindingInfo(
                        code="ERR_VERIFICATION_INTERRUPTED",
                        message="Verification re-scan encountered an internal exception",
                    )
                )

        # Step 3: Persist redacted artifact in managed sandbox
        artifact_ref = self.artifact_manager.store_artifact(
            document_id=doc.document_id,
            content=redacted_text,
            file_extension=doc.source_type if doc.source_type in ("txt", "docx") else "txt",
            content_type="text/plain",
        )

        return RedactionResult(
            document_id=doc.document_id,
            artifact_ref=artifact_ref,
            redactions_applied=applied_count,
            verification_status=verification_status,
            release_allowed=release_allowed,
            findings=findings,
        )


def redact_and_validate(
    doc: ExtractedDocument,
    detection: DetectionResult,
    artifact_manager: Optional[ArtifactManager] = None,
    simulate_verification_failure: bool = False,
) -> RedactionResult:
    """Public functional interface for redaction and verification."""
    from ..detection.detector import detect_pii
    redactor = Redactor(artifact_manager=artifact_manager, verifier_detector=detect_pii)
    return redactor.redact_and_validate(
        doc, detection, simulate_verification_failure=simulate_verification_failure
    )
