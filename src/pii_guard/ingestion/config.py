"""Configuration settings, thresholds, and safety limits for document ingestion."""

import os
import shutil
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field


def resolve_tesseract_binary() -> str:
    """Resolve the Tesseract OCR executable path across platforms."""
    # 1. Explicit environment variable
    env_path = os.getenv("TESSERACT_CMD")
    if env_path and Path(env_path).is_file():
        return env_path

    # 2. System PATH
    which_path = shutil.which("tesseract")
    if which_path:
        return which_path

    # 3. Known default installation candidates
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/opt/homebrew/bin/tesseract",
    ]
    for candidate in candidates:
        if Path(candidate).is_file():
            return str(candidate)

    return "tesseract"


class IngestionConfig(BaseModel):
    """Runtime configuration for document validation, extraction, and OCR."""

    # Resource & Memory Limits
    max_file_size_bytes: int = Field(
        default_factory=lambda: int(os.getenv("INGESTION_MAX_FILE_SIZE_BYTES", 50 * 1024 * 1024)),
        description="50 MB limit",
    )
    max_pages: int = Field(
        default_factory=lambda: int(os.getenv("INGESTION_MAX_PAGES", 500)),
        description="Maximum allowed document pages / slides",
    )
    max_ocr_pages: int = Field(
        default_factory=lambda: int(os.getenv("INGESTION_MAX_OCR_PAGES", 100)),
        description="Max pages permitted to undergo OCR",
    )
    ocr_timeout_per_page_sec: float = Field(
        default_factory=lambda: float(os.getenv("INGESTION_OCR_TIMEOUT_SEC", 10.0)),
        description="Per-page OCR timeout",
    )
    total_timeout_sec: float = Field(
        default_factory=lambda: float(os.getenv("INGESTION_TOTAL_TIMEOUT_SEC", 60.0)),
        description="Total document processing timeout",
    )

    # Zip Bomb Protections (DOCX / PPTX)
    zip_bomb_max_ratio: float = Field(
        default_factory=lambda: float(os.getenv("INGESTION_ZIP_BOMB_MAX_RATIO", 100.0)),
        description="Max compression ratio (uncompressed / compressed)",
    )
    zip_bomb_max_uncompressed_bytes: int = Field(
        default_factory=lambda: int(os.getenv("INGESTION_ZIP_BOMB_MAX_UNCOMPRESSED", 200 * 1024 * 1024)),
        description="200 MB max uncompressed archive size",
    )

    # OCR Tuning & Fast Path
    default_ocr_dpi: int = Field(
        default_factory=lambda: int(os.getenv("INGESTION_DEFAULT_DPI", 200)),
        description="Fast-path rendering DPI",
    )
    fallback_ocr_dpi: int = Field(
        default_factory=lambda: int(os.getenv("INGESTION_FALLBACK_DPI", 300)),
        description="High-resolution fallback DPI",
    )
    min_native_char_density: int = Field(
        default_factory=lambda: int(os.getenv("INGESTION_MIN_CHAR_DENSITY", 50)),
        description="Threshold below which a page is tested for OCR",
    )
    ocr_confidence_threshold: float = Field(
        default_factory=lambda: float(os.getenv("INGESTION_OCR_CONFIDENCE_THRESHOLD", 60.0)),
        description="Confidence threshold below which OCR is flagged as low",
    )
    ocr_engine: str = Field(
        default_factory=lambda: os.getenv("INGESTION_OCR_ENGINE", "tesseract"),
        description="Primary OCR engine: 'tesseract' or 'rapidocr'",
    )
    max_ocr_workers: int = Field(
        default_factory=lambda: int(os.getenv("INGESTION_OCR_WORKERS", max(1, min(4, os.cpu_count() or 1)))),
        description="Bounded process pool workers for parallel page OCR",
    )

    # Binary Paths
    tesseract_cmd: str = Field(default_factory=resolve_tesseract_binary)

    # Text Normalization & Separation
    page_separator: str = Field(default="\f", description="Delimiter separating pages / slides")

    @classmethod
    def from_env(cls) -> "IngestionConfig":
        """Factory method constructing IngestionConfig with active environment overrides."""
        return cls()
