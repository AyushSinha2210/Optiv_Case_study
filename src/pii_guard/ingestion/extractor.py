"""Central orchestration engine for document ingestion, validation, and assembly."""

import uuid
from pathlib import Path
from typing import Optional, List

from .config import IngestionConfig
from .schemas import ExtractedDocument, PageInfo, WarningInfo
from .validator import validate_file
from .router import get_adapter
from .normalize import normalize_text


def extract_document(
    file_path: str, config: Optional[IngestionConfig] = None
) -> ExtractedDocument:
    """Validate, extract, normalize, and assemble document text and offsets.

    CONTRACTUAL GUARANTEES:
    1. NEVER raises an exception to the caller. Fail-closed under all circumstances.
    2. Returned `text` is the single source of truth for downstream PII offsets.
    3. Character spans in `pages[i].start` and `pages[i].end` exactly slice into `text`.
    4. Pages are separated by form feed (`\\f`).
    """
    cfg = config or IngestionConfig()
    doc_id = f"doc-{uuid.uuid4().hex[:12]}"

    if not file_path or not isinstance(file_path, (str, Path)):
        return ExtractedDocument(
            document_id=doc_id,
            source_type="pdf",
            text="",
            pages=[],
            warnings=[
                WarningInfo(
                    code="ERR_INVALID_FILE_PATH",
                    message="Specified file path is empty or of invalid type",
                )
            ],
            extraction_status="failed",
        )

    try:
        # Step 1: Pre-flight validation
        val_res = validate_file(file_path, config=cfg)
        if not val_res.is_valid:
            detected_src = val_res.detected_format or (
                Path(file_path).suffix.lower().lstrip(".")
                if Path(file_path).suffix.lower().lstrip(".") in ("pdf", "docx", "pptx", "txt")
                else "pdf"
            )
            return ExtractedDocument(
                document_id=doc_id,
                source_type=detected_src,
                text="",
                pages=[],
                warnings=[
                    WarningInfo(
                        code=val_res.error_code or "ERR_VALIDATION_FAILED",
                        message=val_res.error_message or "Document failed pre-flight validation",
                    )
                ],
                extraction_status="failed",
            )

        # Step 2: Route to adapter
        adapter = get_adapter(val_res.detected_format)
        adapter_res = adapter.extract(Path(file_path), config=cfg)

        # Step 3: Check for adapter-level failure
        if not adapter_res.pages and adapter_res.warnings:
            return ExtractedDocument(
                document_id=doc_id,
                source_type=adapter_res.source_type,
                text="",
                pages=[],
                warnings=adapter_res.warnings,
                extraction_status="failed",
            )

        # Step 4: Assemble normalized page texts with strict offsets
        assembled_pages: List[PageInfo] = []
        normalized_texts: List[str] = []
        current_offset = 0
        all_warnings: List[WarningInfo] = list(adapter_res.warnings)
        has_partial_signal = False

        CRITICAL_PARTIAL_CODES = {
            "WARN_OCR_LIMIT_REACHED",
            "ERR_OCR_FAILED",
            "WARN_PAGE_CORRUPTED",
            "WARN_CORRUPTED_STREAM",
        }
        has_critical_failure = any(w.code in CRITICAL_PARTIAL_CODES for w in all_warnings)

        for ap in adapter_res.pages:
            norm_page_text = normalize_text(ap.text)
            normalized_texts.append(norm_page_text)
            page_char_count = len(norm_page_text)

            start_offset = current_offset
            end_offset = start_offset + page_char_count

            # Page-level warning propagation
            page_warning_codes = [w.code for w in ap.warnings]
            for w in ap.warnings:
                all_warnings.append(w)
                if w.code in CRITICAL_PARTIAL_CODES:
                    has_partial_signal = True

            assembled_pages.append(
                PageInfo(
                    index=ap.page_num,
                    label=ap.label,
                    start=start_offset,
                    end=end_offset,
                    method=ap.method,
                    ocr_confidence=ap.ocr_confidence,
                    char_count=page_char_count,
                    warnings=page_warning_codes,
                )
            )

            # Advance offset including page separator delimiter
            current_offset = end_offset + len(cfg.page_separator)

        # Construct final single-source-of-truth text
        full_text = cfg.page_separator.join(normalized_texts)

        # Step 5: Determine overall status
        if not full_text.strip():
            extraction_status = "failed"
            all_warnings.append(
                WarningInfo(
                    code="ERR_NO_TEXT_EXTRACTED",
                    message="Document contained no extractable textual content",
                )
            )
        elif has_partial_signal or has_critical_failure:
            extraction_status = "partial"
        else:
            extraction_status = "success"


        return ExtractedDocument(
            document_id=doc_id,
            source_type=adapter_res.source_type,
            text=full_text,
            pages=assembled_pages,
            warnings=all_warnings,
            extraction_status=extraction_status,
        )

    except Exception as e:
        # Fail-closed top-level guard: never raise to caller
        try:
            ext = Path(file_path).suffix.lower().lstrip(".")
            safe_src = ext if ext in ("pdf", "docx", "pptx", "txt") else "pdf"
        except Exception:
            safe_src = "pdf"
        return ExtractedDocument(
            document_id=doc_id,
            source_type=safe_src,
            text="",
            pages=[],
            warnings=[
                WarningInfo(
                    code="ERR_INTERNAL_EXTRACTION_FAILURE",
                    message="An unexpected internal error occurred during document processing",
                )
            ],
            extraction_status="failed",
        )
