"""Format router and adapter registry for document extraction."""

from typing import Dict, Type
from .adapters.base import BaseAdapter
from .adapters.pdf import PDFAdapter
from .adapters.docx import DOCXAdapter
from .adapters.pptx import PPTXAdapter
from .adapters.txt import TXTAdapter
from .adapters.json_adapter import JSONAdapter
from .adapters.image import ImageAdapter

# Registry of format adapters
_ADAPTER_REGISTRY: Dict[str, Type[BaseAdapter]] = {
    "pdf": PDFAdapter,
    "docx": DOCXAdapter,
    "pptx": PPTXAdapter,
    "txt": TXTAdapter,
    "json": JSONAdapter,
    "image": ImageAdapter,
    "png": ImageAdapter,
    "jpg": ImageAdapter,
    "jpeg": ImageAdapter,
}


def register_adapter(format_name: str, adapter_cls: Type[BaseAdapter]) -> None:
    """Register a new format adapter in the pipeline."""
    _ADAPTER_REGISTRY[format_name.lower()] = adapter_cls


def get_adapter(format_name: str) -> BaseAdapter:
    """Instantiate and return the appropriate adapter for the format."""
    adapter_cls = _ADAPTER_REGISTRY.get(format_name.lower())
    if not adapter_cls:
        raise ValueError(f"No adapter registered for format: {format_name}")
    return adapter_cls()
