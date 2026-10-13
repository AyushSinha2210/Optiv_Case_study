"""Pipeline state definitions and transition management.

Enforces valid lifecycle transitions and records an immutable audit history of states.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict

from .errors import InvalidStateTransitionError


class PipelineStage(str, Enum):
    """Sequential operational stages in the PII Guard pipeline."""
    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    EXTRACTED = "EXTRACTED"
    DETECTED = "DETECTED"
    REDACTED = "REDACTED"
    VERIFIED = "VERIFIED"
    RELEASED = "RELEASED"
    # Terminal fault / blocked stages
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    INCOMPLETE = "INCOMPLETE"


class TerminalStatus(str, Enum):
    """High-level outcome status for pipeline execution."""
    SUCCESS = "success"
    BLOCKED = "blocked"
    FAILED = "failed"
    INCOMPLETE = "incomplete"


class StageTransition(BaseModel):
    """Immutable record of an individual stage transition."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    from_stage: Optional[PipelineStage] = Field(
        default=None, description="Previous pipeline stage, or None if initial stage"
    )
    to_stage: PipelineStage = Field(
        ..., description="Newly reached pipeline stage"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timezone-aware UTC timestamp of the transition"
    )
    message: Optional[str] = Field(
        default=None, description="Safe status or transition reason description"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Safe metadata attributes (no PII or raw text)"
    )


class PipelineStateManager:
    """Manages legal stage transitions and records transition history."""

    # Set of permitted sequential forward transitions
    _LEGAL_SEQUENTIAL_TRANSITIONS: Dict[Optional[PipelineStage], List[PipelineStage]] = {
        None: [PipelineStage.RECEIVED, PipelineStage.FAILED],
        PipelineStage.RECEIVED: [PipelineStage.VALIDATED, PipelineStage.FAILED, PipelineStage.INCOMPLETE],
        PipelineStage.VALIDATED: [PipelineStage.EXTRACTED, PipelineStage.FAILED, PipelineStage.INCOMPLETE],
        PipelineStage.EXTRACTED: [PipelineStage.DETECTED, PipelineStage.FAILED, PipelineStage.INCOMPLETE],
        PipelineStage.DETECTED: [PipelineStage.REDACTED, PipelineStage.FAILED, PipelineStage.INCOMPLETE],
        PipelineStage.REDACTED: [PipelineStage.VERIFIED, PipelineStage.BLOCKED, PipelineStage.FAILED, PipelineStage.INCOMPLETE],
        PipelineStage.VERIFIED: [PipelineStage.RELEASED, PipelineStage.BLOCKED, PipelineStage.FAILED, PipelineStage.INCOMPLETE],
        # Terminal states allow no further forward transitions
        PipelineStage.RELEASED: [],
        PipelineStage.BLOCKED: [],
        PipelineStage.FAILED: [],
        PipelineStage.INCOMPLETE: [],
    }

    def __init__(self, initial_stage: Optional[PipelineStage] = None):
        self._history: List[StageTransition] = []
        self._current_stage: Optional[PipelineStage] = None
        if initial_stage is not None:
            self.transition_to(initial_stage, message="Initial pipeline stage set")

    @property
    def current_stage(self) -> Optional[PipelineStage]:
        """Current active stage."""
        return self._current_stage

    @property
    def history(self) -> List[StageTransition]:
        """Immutable list of state transitions."""
        return list(self._history)

    def can_transition_to(self, target_stage: PipelineStage) -> bool:
        """Check if transitioning from current stage to target stage is permitted."""
        allowed = self._LEGAL_SEQUENTIAL_TRANSITIONS.get(self._current_stage, [])
        return target_stage in allowed

    def transition_to(
        self,
        target_stage: PipelineStage,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StageTransition:
        """Transition pipeline to target_stage if legal, recording the event."""
        if not self.can_transition_to(target_stage):
            curr_str = self._current_stage.value if self._current_stage else "None"
            raise InvalidStateTransitionError(
                f"Illegal state transition from {curr_str} to {target_stage.value}"
            )

        transition = StageTransition(
            from_stage=self._current_stage,
            to_stage=target_stage,
            timestamp=datetime.now(timezone.utc),
            message=message,
            metadata=metadata or {},
        )
        self._history.append(transition)
        self._current_stage = target_stage
        return transition

    def transition_to_failed(self, message: str, safe_code: str = "ERR_PIPELINE_FAILED") -> StageTransition:
        """Helper to safely abort pipeline into FAILED state from any non-terminal state."""
        return self.transition_to(
            PipelineStage.FAILED,
            message=message,
            metadata={"error_code": safe_code},
        )

    def transition_to_blocked(self, message: str, reason_code: str = "WARN_RELEASE_BLOCKED") -> StageTransition:
        """Helper to transition pipeline into BLOCKED state when verification fails."""
        return self.transition_to(
            PipelineStage.BLOCKED,
            message=message,
            metadata={"reason_code": reason_code},
        )
