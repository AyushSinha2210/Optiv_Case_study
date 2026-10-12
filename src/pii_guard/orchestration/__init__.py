"""PII Guard Orchestration & State Management Module.

Owned by Member 5 (Tirth). Coordinates ingestion, detection, redaction,
verification, release authorization, and metadata audit trail.
"""

from .state import PipelineStage, TerminalStatus, StageTransition, PipelineStateManager
from .errors import (
    PipelineError,
    ValidationError,
    UnsupportedFileTypeError,
    FileTooLargeError,
    DocumentReadError,
    ExtractionError,
    DetectionError,
    RedactionError,
    VerificationError,
    ReleaseGateBlockedError,
    ArtifactAccessError,
    InternalProcessingError,
    InvalidStateTransitionError,
    sanitize_error_message,
)
from .models import (
    DetectedEntity,
    DetectionResult,
    FindingInfo,
    RedactionResult,
    ProcessingResult,
)

__all__ = [
    "PipelineStage",
    "TerminalStatus",
    "StageTransition",
    "PipelineStateManager",
    "PipelineError",
    "ValidationError",
    "UnsupportedFileTypeError",
    "FileTooLargeError",
    "DocumentReadError",
    "ExtractionError",
    "DetectionError",
    "RedactionError",
    "VerificationError",
    "ReleaseGateBlockedError",
    "ArtifactAccessError",
    "InternalProcessingError",
    "InvalidStateTransitionError",
    "sanitize_error_message",
    "DetectedEntity",
    "DetectionResult",
    "FindingInfo",
    "RedactionResult",
    "ProcessingResult",
]
