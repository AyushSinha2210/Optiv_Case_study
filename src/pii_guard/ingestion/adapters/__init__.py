"""Format-specific adapters for text extraction."""

from .base import BaseAdapter, AdapterPage, AdapterResult
from .pdf import PDFAdapter
from .docx import DOCXAdapter
from .pptx import PPTXAdapter
from .txt import TXTAdapter
from .json_adapter import JSONAdapter
from .image import ImageAdapter

__all__ = [
    "BaseAdapter",
    "AdapterPage",
    "AdapterResult",
    "PDFAdapter",
    "DOCXAdapter",
    "PPTXAdapter",
    "TXTAdapter",
    "JSONAdapter",
    "ImageAdapter",
]
