"""High-performance PDF adapter using PyMuPDF with selective per-page OCR."""

from pathlib import Path
from typing import List, Optional
from PIL import Image

from .base import BaseAdapter, AdapterPage, AdapterResult
from ..config import IngestionConfig
from ..schemas import WarningInfo
from ..ocr import get_ocr_engine


class PDFAdapter(BaseAdapter):
    """Layout-aware PDF extractor using PyMuPDF (fitz) with lazy imports and selective OCR."""

    def extract(self, path: Path, config: IngestionConfig) -> AdapterResult:
        import pymupdf  # Lazy import heavy library

        doc = pymupdf.open(str(path))
        num_pages = len(doc)
        warnings: List[WarningInfo] = []

        if num_pages > config.max_pages:
            doc.close()
            return AdapterResult(
                pages=[],
                warnings=[
                    WarningInfo(
                        code="ERR_PAGE_LIMIT_EXCEEDED",
                        message=f"Document page count ({num_pages}) exceeds maximum allowed limit ({config.max_pages})",
                    )
                ],
                source_type="pdf",
            )

        ocr_engine = get_ocr_engine(config)
        pages: List[AdapterPage] = []
        ocr_page_count = 0
        total_ocr_pages = 0

        for page_idx in range(num_pages):
            page_num = page_idx + 1
            page = doc[page_idx]

            # 1. Native text extraction via block sorting
            # Blocks: (x0, y0, x1, y1, text, block_no, block_type)
            # block_type 0 = text, 1 = image
            blocks = page.get_text("blocks")
            text_blocks = [b for b in blocks if b[6] == 0 and b[4].strip()]

            # Sort blocks in reading order: top-to-bottom, left-to-right
            text_blocks.sort(key=lambda b: (b[1], b[0]))
            native_text = "\n\n".join(b[4].strip() for b in text_blocks).strip()
            native_char_count = len(native_text)

            page_images = page.get_images()
            needs_ocr = False

            # Trigger OCR if text is sparse and images are present, or text is virtually absent
            if native_char_count < config.min_native_char_density:
                if page_images or native_char_count == 0:
                    needs_ocr = True

            if needs_ocr and ocr_page_count < config.max_ocr_pages:
                ocr_page_count += 1
                total_ocr_pages += 1
                # Render page at 200 DPI fast path
                pix = page.get_pixmap(dpi=config.default_ocr_dpi)
                mode = "RGBA" if pix.alpha else "RGB"
                img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
                if mode == "RGBA":
                    img = img.convert("RGB")

                ocr_res = ocr_engine.process_image(img, page_num=page_num, config=config)

                if native_char_count > 0 and ocr_res.text:
                    # Mixed page: native text plus OCR
                    final_text = f"{native_text}\n\n{ocr_res.text}".strip()
                    method = "mixed"
                else:
                    final_text = ocr_res.text if ocr_res.text else native_text
                    method = "ocr" if ocr_res.text else "native"

                pages.append(
                    AdapterPage(
                        page_num=page_num,
                        label="page",
                        text=final_text,
                        method=method,
                        ocr_confidence=ocr_res.confidence,
                        warnings=ocr_res.warnings,
                    )
                )
            else:
                if needs_ocr and ocr_page_count >= config.max_ocr_pages:
                    warnings.append(
                        WarningInfo(
                            code="WARN_OCR_LIMIT_REACHED",
                            page=page_num,
                            message="Maximum OCR page quota reached; skipping remaining OCR candidates",
                        )
                    )

                pages.append(
                    AdapterPage(
                        page_num=page_num,
                        label="page",
                        text=native_text,
                        method="native",
                        ocr_confidence=None,
                        warnings=[],
                    )
                )

        doc.close()

        # Classify overall source type
        is_scanned = (
            total_ocr_pages > 0 and all(p.method in ("ocr", "mixed") for p in pages)
        )
        source_type = "scanned_pdf" if is_scanned else "pdf"

        return AdapterResult(pages=pages, warnings=warnings, source_type=source_type)
