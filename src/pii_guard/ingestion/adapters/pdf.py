import concurrent.futures
from pathlib import Path
from typing import List, Optional, Dict, Any
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

        # Phase 1: Rapid layout scanning and candidate identification
        ocr_candidates: List[tuple[int, int, str, int, Image.Image]] = []
        page_records: List[Dict[str, Any]] = []
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

                ocr_candidates.append((page_idx, page_num, native_text, native_char_count, img))
                page_records.append({
                    "page_num": page_num,
                    "needs_ocr": True,
                    "native_text": native_text,
                    "native_char_count": native_char_count,
                })
            else:
                if needs_ocr and ocr_page_count >= config.max_ocr_pages:
                    warnings.append(
                        WarningInfo(
                            code="WARN_OCR_LIMIT_REACHED",
                            page=page_num,
                            message="Maximum OCR page quota reached; skipping remaining OCR candidates",
                        )
                    )

                page_records.append({
                    "page_num": page_num,
                    "needs_ocr": False,
                    "native_text": native_text,
                    "native_char_count": native_char_count,
                })

        doc.close()

        # Phase 2: Parallel OCR execution across worker pool
        ocr_results_by_idx: Dict[int, Any] = {}
        if ocr_candidates:
            ocr_engine = None
            try:
                ocr_engine = get_ocr_engine(config)
            except Exception:
                warnings.append(
                    WarningInfo(
                        code="WARN_OCR_UNAVAILABLE",
                        message="OCR engine could not be initialized; skipping OCR extraction",
                    )
                )

            if ocr_engine:
                max_workers = min(config.max_ocr_workers, len(ocr_candidates), 8)

                def _execute_page_ocr(cand: tuple[int, int, str, int, Image.Image]):
                    p_idx, p_num, _, _, page_img = cand
                    ocr_res = ocr_engine.process_image(page_img, page_num=p_num, config=config)
                    return p_idx, ocr_res

                if max_workers > 1 and len(ocr_candidates) > 1:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                        for p_idx, res in executor.map(_execute_page_ocr, ocr_candidates):
                            ocr_results_by_idx[p_idx] = res
                else:
                    for cand in ocr_candidates:
                        p_idx, res = _execute_page_ocr(cand)
                        ocr_results_by_idx[p_idx] = res

        # Phase 3: Ordered assembly of pages preserving exact document structure
        pages: List[AdapterPage] = []
        for page_idx, rec in enumerate(page_records):
            page_num = rec["page_num"]
            native_text = rec["native_text"]
            native_char_count = rec["native_char_count"]

            if rec["needs_ocr"] and page_idx in ocr_results_by_idx:
                ocr_res = ocr_results_by_idx[page_idx]
                if native_char_count > 0 and ocr_res.text:
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

        # Classify overall source type
        is_scanned = (
            total_ocr_pages > 0 and all(p.method in ("ocr", "mixed") for p in pages)
        )
        source_type = "scanned_pdf" if is_scanned else "pdf"

        return AdapterResult(pages=pages, warnings=warnings, source_type=source_type)
