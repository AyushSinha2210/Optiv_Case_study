"""Public data contracts and schemas for the PII Guard ingestion module.

Teammates (Detection, Redaction, Integration) depend directly on this contract.
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class PageInfo(BaseModel):
    """Metadata and character span boundaries for a single page or slide.

    Offsets are 0-based, end-exclusive indices into `ExtractedDocument.text`.
    """
    model_config = ConfigDict(extra="forbid")

    index: int = Field(..., description="1-based page or slide index")
    label: Literal["page", "slide"] = Field(
        ..., description="'page' for PDF/DOCX/TXT, 'slide' for PPTX"
    )
    start: int = Field(
        ..., description="0-based start character offset into ExtractedDocument.text"
    )
    end: int = Field(
        ..., description="0-based end character offset (exclusive) into ExtractedDocument.text"
    )
    method: Literal["native", "ocr", "mixed"] = Field(
        ..., description="Extraction method used for this page"
    )
    ocr_confidence: Optional[float] = Field(
        default=None,
        description="Mean OCR confidence percentage (0.0 - 100.0), or None for purely native",
    )
    char_count: int = Field(..., description="Total character count within this page boundary")
    warnings: List[str] = Field(
        default_factory=list, description="Warning codes specific to this page"
    )


class WarningInfo(BaseModel):
    """Structured, safe warning record.

    CRITICAL PRIVACY RULE: Warning messages MUST NEVER contain document text,
    snippets, or entity values.
    """
    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., description="Machine-readable error/warning code")
    page: Optional[int] = Field(default=None, description="1-based page index if applicable")
    message: str = Field(
        ..., description="Sanitized, human-readable description with zero document text"
    )


class ExtractedDocument(BaseModel):
    """Canonical extraction contract for downstream PII Guard pipeline modules.

    `text` is the single source of truth for downstream detection and redaction offsets.
    """
    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(..., description="Unique document UUID identifier")
    source_type: Literal["pdf", "scanned_pdf", "docx", "pptx", "txt"] = Field(
        ..., description="Verified document format classification"
    )
    text: str = Field(
        ..., description="Exact extracted and normalized text used by downstream offsets"
    )
    pages: List[PageInfo] = Field(
        default_factory=list, description="Per-page/slide structural metadata and offsets"
    )
    warnings: List[WarningInfo] = Field(
        default_factory=list, description="Structured warnings encountered during processing"
    )
    extraction_status: Literal["success", "partial", "failed"] = Field(
        ..., description="Overall extraction outcome"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to standard Python dictionary for pipeline interoperability."""
        return self.model_dump()
