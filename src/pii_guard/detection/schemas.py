"""Contract B (DetectionResult) models and internal candidate type.

Owned by Member 2 (Avishi Sharma). Offsets are zero-based, end-exclusive
indices into ExtractedDocument.text.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict, Field, model_validator

PIIType = Literal[
    "PERSON",
    "EMAIL",
    "PHONE",
    "ADDRESS",
    "GOVERNMENT_ID",
    "FINANCIAL_IDENTIFIER",
    "IP_ADDRESS",
    "EMPLOYEE_ID",
]
PII_TYPES: frozenset[str] = frozenset(get_args(PIIType))


class DetectedEntity(BaseModel):
    """One classified PII span. Contract B, entities[]."""

    model_config = ConfigDict(extra="forbid")

    type: PIIType
    start: int = Field(..., ge=0)
    end: int = Field(..., ge=0)
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Detector score in [0, 1]; a rule-match score, not a proof of correctness.",
    )

    @model_validator(mode="after")
    def _check_span(self) -> "DetectedEntity":
        if self.end <= self.start:
            raise ValueError("end must be greater than start")
        return self


class DetectionWarning(BaseModel):
    """Safe warning. The message never contains document text or matched values."""

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str


class DetectionResult(BaseModel):
    """Contract B: output of detect_pii()."""

    model_config = ConfigDict(extra="forbid")

    document_id: str
    entities: list[DetectedEntity] = Field(default_factory=list)
    warnings: list[DetectionWarning] = Field(default_factory=list)


class DetectionInputError(ValueError):
    """Raised when detection must not run (fail-closed), e.g. upstream extraction failed."""


@dataclass(frozen=True)
class Candidate:
    """Internal span proposal before overlap resolution. Never leaves the module."""

    type: str
    start: int
    end: int
    confidence: float
    source: str  # "pattern" or "ner"
