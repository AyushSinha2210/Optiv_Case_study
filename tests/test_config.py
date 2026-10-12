"""Unit tests for IngestionConfig and Tesseract path resolution."""

import os
from src.pii_guard.ingestion.config import IngestionConfig, resolve_tesseract_binary


def test_default_config_values():
    """Verify standard default configuration parameters and limits."""
    cfg = IngestionConfig()
    assert cfg.max_file_size_bytes == 50 * 1024 * 1024
    assert cfg.max_pages == 500
    assert cfg.max_ocr_pages == 100
    assert cfg.ocr_timeout_per_page_sec == 10.0
    assert cfg.default_ocr_dpi == 200
    assert cfg.fallback_ocr_dpi == 300
    assert cfg.ocr_confidence_threshold == 60.0
    assert cfg.zip_bomb_max_ratio == 100.0
    assert cfg.page_separator == "\f"


def test_config_env_overrides(monkeypatch):
    """Verify environment variables dynamically override configuration limits."""
    monkeypatch.setenv("INGESTION_MAX_FILE_SIZE_BYTES", "1048576")
    monkeypatch.setenv("INGESTION_MAX_PAGES", "50")
    monkeypatch.setenv("INGESTION_DEFAULT_DPI", "150")
    monkeypatch.setenv("INGESTION_OCR_CONFIDENCE_THRESHOLD", "75.0")

    cfg = IngestionConfig.from_env()
    assert cfg.max_file_size_bytes == 1048576
    assert cfg.max_pages == 50
    assert cfg.default_ocr_dpi == 150
    assert cfg.ocr_confidence_threshold == 75.0


def test_resolve_tesseract_binary_env(monkeypatch, tmp_path):
    """Verify TESSERACT_CMD environment variable takes precedence."""
    fake_bin = tmp_path / "mock_tesseract.exe"
    fake_bin.write_text("binary")
    monkeypatch.setenv("TESSERACT_CMD", str(fake_bin))

    resolved = resolve_tesseract_binary()
    assert resolved == str(fake_bin)
