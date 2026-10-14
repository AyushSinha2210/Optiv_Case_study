"""Contract C: typed output from Member 3."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RedactionFinding(BaseModel):
    """Safe metadata about a check; never contains a source value or snippet."""

    model_config = ConfigDict(extra="forbid")

    check: str
    entity_type: str | None = None
    count: int | None = Field(default=None, ge=0)
    message: str | None = None


class RedactionResult(BaseModel):
    """Contract C consumed by Member 5."""

    model_config = ConfigDict(extra="forbid")

    document_id: str
    artifact_ref: str | None = None
    redactions_applied: int = Field(..., ge=0)
    verification_status: Literal["PASS", "FAIL", "INCOMPLETE"]
    release_allowed: bool
    findings: list[RedactionFinding] = Field(default_factory=list)
    structure_score: float | None = None
