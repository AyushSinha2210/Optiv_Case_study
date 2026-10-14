"""Canonical data models for cross-module pipeline integration.

Conforms strictly to Section 10 Contract Specifications in `docs/interfaces.md`.
"""

from typing import List, Optional, Literal, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict

from .state import PipelineStage, TerminalStatus, StageTransition


class DetectedEntity(BaseModel):
    """Classified PII entity span matching Contract B."""
    model_config = ConfigDict(extra="forbid")

    type: str = Field(..., description="Standard PII category label")
    start: int = Field(..., description="0-based character start offset into ExtractedDocument.text")
    end: int = Field(..., description="0-based character end offset (exclusive)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")


class DetectionResult(BaseModel):
    """Canonical Contract B model (Member 2 -> Member 3)."""
    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(..., description="Unique document UUID")
    entities: List[DetectedEntity] = Field(default_factory=list, description="Classified PII spans")
    warnings: List[str] = Field(default_factory=list, description="Safe warning codes")


class FindingInfo(BaseModel):
    """Safe verification or redaction finding."""
    model_config = ConfigDict(extra="ignore")

    code: str = Field(default="INFO", description="Machine-readable code")
    message: str = Field(default="", description="Sanitized description without document text")
    category: Optional[str] = Field(default=None, description="Associated PII category if known")
    check: Optional[str] = Field(default=None, description="Check identifier")
    entity_type: Optional[str] = Field(default=None, description="Entity type")
    count: Optional[int] = Field(default=None, description="Count")


class RedactionResult(BaseModel):
    """Canonical Contract C model (Member 3 -> Member 5)."""
    model_config = ConfigDict(extra="ignore")

    document_id: str = Field(..., description="Unique document UUID")
    artifact_ref: Optional[str] = Field(
        default=None, description="Opaque token or protected reference to sanitized artifact"
    )
    redactions_applied: int = Field(default=0, ge=0, description="Count of masked entities")
    verification_status: Literal["PASS", "FAIL", "INCOMPLETE"] = Field(
        ..., description="Verification gate outcome"
    )
    release_allowed: bool = Field(
        default=False, description="Strict release permission flag"
    )
    findings: List[Any] = Field(default_factory=list, description="Safe findings")
    structure_score: Optional[float] = Field(default=None, description="Structural retention score")


class ProcessingReport(BaseModel):
    """Canonical Contract D audit ledger (Member 5 -> Client/Auditor)."""
    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(..., description="Unique document UUID")
    workflow_status: Literal["success", "blocked", "failed", "incomplete"] = Field(...)
    category_counts: Dict[str, int] = Field(default_factory=dict, description="Counts of detected PII by category")
    verification_status: Literal["PASS", "FAIL", "INCOMPLETE"] = Field(...)
    release_allowed: bool = Field(default=False, description="Strict release authorization decision")
    precision: float = Field(default=1.0, ge=0.0, le=1.0, description="PII detection precision score")
    recall: float = Field(default=1.0, ge=0.0, le=1.0, description="PII detection recall score")
    f1_score: float = Field(default=1.0, ge=0.0, le=1.0, description="PII detection F1 harmonic score")
    false_negative_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="False negative rate (residual leakage)")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timezone-aware creation timestamp"
    )
    processing_duration_sec: float = Field(default=0.0, ge=0.0)
    module_versions: Dict[str, str] = Field(
        default_factory=lambda: {
            "ingestion": "1.0.0",
            "detection": "1.0.0",
            "redaction": "1.0.0",
            "orchestration": "1.0.0",
        }
    )
    safe_warnings: List[str] = Field(default_factory=list)
    safe_error: Optional[str] = Field(default=None)


class ProcessingResult(BaseModel):
    """Public return model for pipeline execution coordinator."""
    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(..., description="Unique document UUID")
    workflow_status: Literal["success", "blocked", "failed", "incomplete"] = Field(
        ..., description="Overall pipeline outcome"
    )
    current_stage: PipelineStage = Field(..., description="Final pipeline stage reached")
    stage_history: List[StageTransition] = Field(default_factory=list, description="Lifecycle transitions")
    started_at: datetime = Field(..., description="Pipeline execution start timestamp (UTC)")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp (UTC)")
    
    # Per-stage safe telemetry
    source_type: Optional[str] = Field(default=None, description="Document type: pdf, docx, etc.")
    pages_count: int = Field(default=0, ge=0, description="Total pages/slides processed")
    char_count: int = Field(default=0, ge=0, description="Total characters processed")
    
    extraction_status: Optional[str] = Field(default=None)
    detection_status: Optional[str] = Field(default=None)
    redaction_status: Optional[str] = Field(default=None)
    verification_status: Optional[str] = Field(default=None)
    release_allowed: bool = Field(default=False)
    precision: float = Field(default=1.0, ge=0.0, le=1.0, description="PII detection precision score")
    recall: float = Field(default=1.0, ge=0.0, le=1.0, description="PII detection recall score")
    f1_score: float = Field(default=1.0, ge=0.0, le=1.0, description="PII detection F1 harmonic score")
    false_negative_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="False negative rate (residual leakage)")
    
    category_counts: Dict[str, int] = Field(default_factory=dict)
    redactions_applied: int = Field(default=0, ge=0)
    
    safe_warnings: List[str] = Field(default_factory=list)
    safe_error: Optional[str] = Field(default=None)
    safe_error_code: Optional[str] = Field(default=None)
    
    artifact_ref: Optional[str] = Field(default=None)
    audit_id: Optional[str] = Field(default=None)
    report_id: Optional[str] = Field(default=None)
    verification_findings: List[Dict[str, Any]] = Field(default_factory=list, description="Sanitized verification fault findings")
    structure_score: Optional[float] = Field(default=None, description="Structural retention score")

    def to_safe_dict(self) -> Dict[str, Any]:
        """Serialize exclusively safe fields for UI/API delivery.
        
        GUARANTEE: Zero document text, zero detected PII values, zero internal absolute paths.
        """
        return {
            "document_id": self.document_id,
            "workflow_status": self.workflow_status,
            "current_stage": self.current_stage.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "source_type": self.source_type,
            "pages_count": self.pages_count,
            "char_count": self.char_count,
            "extraction_status": self.extraction_status,
            "detection_status": self.detection_status,
            "redaction_status": self.redaction_status,
            "verification_status": self.verification_status,
            "release_allowed": self.release_allowed,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1_score, 4),
            "false_negative_rate": round(self.false_negative_rate, 4),
            "category_counts": dict(self.category_counts),
            "redactions_applied": self.redactions_applied,
            "safe_warnings": list(self.safe_warnings),
            "safe_error": self.safe_error,
            "safe_error_code": self.safe_error_code,
            "artifact_ref": self.artifact_ref if self.release_allowed else None,
            "audit_id": self.audit_id,
            "report_id": self.report_id,
            "verification_findings": list(self.verification_findings),
            "structure_score": self.structure_score,
        }
