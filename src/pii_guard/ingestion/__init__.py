"""PII Guard Ingestion Module.

Owned by Member 1 (Ayush Sinha). Provides secure multi-format document
validation, layout-preserving extraction, and selective page OCR.
"""

from .schemas import ExtractedDocument, PageInfo, WarningInfo
from .config import IngestionConfig

__all__ = [
    "extract_document",
    "ExtractedDocument",
    "PageInfo",
    "WarningInfo",
    "IngestionConfig",
]

# extract_document will be imported from .extractor once implemented
def extract_document(file_path: str, config: IngestionConfig = None) -> ExtractedDocument:
    from .extractor import extract_document as _extract
    return _extract(file_path, config=config)
