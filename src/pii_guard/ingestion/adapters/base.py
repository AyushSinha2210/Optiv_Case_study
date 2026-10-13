"""Base interface and data models for document format adapters."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from ..config import IngestionConfig
from ..schemas import WarningInfo


class AdapterPage(BaseModel):
    """Raw extracted content for an individual page or slide before global assembly."""
    page_num: int
    label: Literal["page", "slide"] = "page"
    text: str
    method: Literal["native", "ocr", "mixed"] = "native"
    ocr_confidence: Optional[float] = None
    warnings: List[WarningInfo] = Field(default_factory=list)


class AdapterResult(BaseModel):
    """Aggregated output from a format adapter."""
    pages: List[AdapterPage]
    warnings: List[WarningInfo] = Field(default_factory=list)
    source_type: Literal["pdf", "scanned_pdf", "docx", "pptx", "txt", "json", "image"]


class BaseAdapter(ABC):
    """Abstract base class that all format extractors must implement."""

    @abstractmethod
    def extract(self, path: Path, config: IngestionConfig) -> AdapterResult:
        """Extract text and metadata from the document file."""
        pass
