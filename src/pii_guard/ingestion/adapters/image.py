"""Image document adapter for PNG, JPEG, and scanned image artifacts."""

from pathlib import Path
from typing import List
from PIL import Image

from .base import BaseAdapter, AdapterPage, AdapterResult
from ..config import IngestionConfig
from ..schemas import WarningInfo
from ..ocr import get_ocr_engine


class ImageAdapter(BaseAdapter):
    """Adapter for image files (PNG, JPEG) utilizing OCR and layout bounding analysis."""

    def extract(self, path: Path, config: IngestionConfig) -> AdapterResult:
        warnings: List[WarningInfo] = []
        try:
            with Image.open(path) as img:
                width, height = img.size
                format_name = img.format or path.suffix.lstrip(".").upper()
                rgb_img = img.convert("RGB")
        except Exception as e:
            return AdapterResult(
                pages=[],
                warnings=[
                    WarningInfo(
                        code="ERR_CORRUPT_FILE",
                        message="Image file header corrupted or unreadable",
                    )
                ],
                source_type="image",
            )

        extracted_text = ""
        ocr_confidence = None
        method = "ocr"

        try:
            ocr_engine = get_ocr_engine(config)
            ocr_res = ocr_engine.process_image(rgb_img, page_num=1, config=config)
            extracted_text = (ocr_res.text or "").strip()
            ocr_confidence = ocr_res.confidence
            warnings.extend(ocr_res.warnings)
        except Exception:
            warnings.append(
                WarningInfo(
                    code="WARN_OCR_UNAVAILABLE",
                    page=1,
                    message="OCR engine unavailable or OCR extraction skipped for image",
                )
            )

        if not extracted_text:
            extracted_text = f"[IMAGE_METADATA: Format={format_name}, Resolution={width}x{height}]"

        page = AdapterPage(
            page_num=1,
            label="page",
            text=extracted_text,
            method="ocr" if ocr_confidence is not None else "native",
            ocr_confidence=ocr_confidence,
            warnings=warnings,
        )

        return AdapterResult(
            pages=[page],
            warnings=warnings,
            source_type="image",
        )
