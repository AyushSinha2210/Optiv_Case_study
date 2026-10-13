"""Unit tests for PipelineStage and PipelineStateManager."""

import pytest
from src.pii_guard.orchestration.state import (
    PipelineStage,
    PipelineStateManager,
    InvalidStateTransitionError,
)


def test_initial_state_none():
    """Manager initialized with no stage starts with None."""
    sm = PipelineStateManager()
    assert sm.current_stage is None
    assert len(sm.history) == 0


def test_initial_state_received():
    """Manager initialized with RECEIVED records initial transition."""
    sm = PipelineStateManager(initial_stage=PipelineStage.RECEIVED)
    assert sm.current_stage == PipelineStage.RECEIVED
    assert len(sm.history) == 1
    assert sm.history[0].to_stage == PipelineStage.RECEIVED
    assert sm.history[0].from_stage is None


def test_legal_happy_path_transitions():
    """Sequential forward transitions must succeed through RELEASED."""
    sm = PipelineStateManager(initial_stage=PipelineStage.RECEIVED)

    sm.transition_to(PipelineStage.VALIDATED)
    assert sm.current_stage == PipelineStage.VALIDATED

    sm.transition_to(PipelineStage.EXTRACTED)
    assert sm.current_stage == PipelineStage.EXTRACTED

    sm.transition_to(PipelineStage.DETECTED)
    assert sm.current_stage == PipelineStage.DETECTED

    sm.transition_to(PipelineStage.REDACTED)
    assert sm.current_stage == PipelineStage.REDACTED

    sm.transition_to(PipelineStage.VERIFIED)
    assert sm.current_stage == PipelineStage.VERIFIED

    sm.transition_to(PipelineStage.RELEASED)
    assert sm.current_stage == PipelineStage.RELEASED

    assert len(sm.history) == 7


def test_reject_illegal_transition_skip_stage():
    """Attempting to skip stages (e.g. RECEIVED -> RELEASED) must raise error."""
    sm = PipelineStateManager(initial_stage=PipelineStage.RECEIVED)
    with pytest.raises(InvalidStateTransitionError):
        sm.transition_to(PipelineStage.RELEASED)


def test_reject_backward_transition():
    """Backwards transitions (e.g. DETECTED -> VALIDATED) must be rejected."""
    sm = PipelineStateManager(initial_stage=PipelineStage.RECEIVED)
    sm.transition_to(PipelineStage.VALIDATED)
    sm.transition_to(PipelineStage.EXTRACTED)
    sm.transition_to(PipelineStage.DETECTED)

    with pytest.raises(InvalidStateTransitionError):
        sm.transition_to(PipelineStage.VALIDATED)


def test_transition_to_blocked_from_verified():
    """Failed verification can legally transition VERIFIED to BLOCKED."""
    sm = PipelineStateManager(initial_stage=PipelineStage.RECEIVED)
    sm.transition_to(PipelineStage.VALIDATED)
    sm.transition_to(PipelineStage.EXTRACTED)
    sm.transition_to(PipelineStage.DETECTED)
    sm.transition_to(PipelineStage.REDACTED)
    sm.transition_to(PipelineStage.VERIFIED)

    trans = sm.transition_to_blocked("Verification detected residual PII")
    assert sm.current_stage == PipelineStage.BLOCKED
    assert trans.to_stage == PipelineStage.BLOCKED
    assert trans.metadata["reason_code"] == "WARN_RELEASE_BLOCKED"


def test_transition_to_failed_from_any_stage():
    """Any non-terminal stage can transition to FAILED."""
    sm = PipelineStateManager(initial_stage=PipelineStage.RECEIVED)
    sm.transition_to(PipelineStage.VALIDATED)
    sm.transition_to(PipelineStage.EXTRACTED)

    trans = sm.transition_to_failed("Extraction parser crashed")
    assert sm.current_stage == PipelineStage.FAILED
    assert trans.to_stage == PipelineStage.FAILED


def test_terminal_states_disallow_further_transitions():
    """Terminal states (RELEASED, BLOCKED, FAILED, INCOMPLETE) must reject transitions."""
    # Test FAILED
    sm1 = PipelineStateManager(initial_stage=PipelineStage.RECEIVED)
    sm1.transition_to_failed("Fatal error")
    with pytest.raises(InvalidStateTransitionError):
        sm1.transition_to(PipelineStage.RELEASED)

    # Test BLOCKED
    sm2 = PipelineStateManager(initial_stage=PipelineStage.RECEIVED)
    sm2.transition_to(PipelineStage.VALIDATED)
    sm2.transition_to(PipelineStage.EXTRACTED)
    sm2.transition_to(PipelineStage.DETECTED)
    sm2.transition_to(PipelineStage.REDACTED)
    sm2.transition_to(PipelineStage.BLOCKED)
    with pytest.raises(InvalidStateTransitionError):
        sm2.transition_to(PipelineStage.RELEASED)
