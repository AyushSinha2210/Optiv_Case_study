"""Secure document validation, format sniffing, and malicious artifact defenses."""

import os
import zipfile
from pathlib import Path
from typing import Optional, List, Tuple
from pydantic import BaseModel, Field

from .config import IngestionConfig
from .schemas import WarningInfo


class ValidationResult(BaseModel):
    """Output of document pre-flight validation."""
    is_valid: bool
    detected_format: Optional[str] = None  # "pdf", "docx", "pptx", "txt"
    warnings: List[WarningInfo] = Field(default_factory=list)
    error_code: Optional[str] = None
    error_message: Optional[str] = None


# Magic byte signatures
MAGIC_PDF = b"%PDF-"
MAGIC_ZIP = b"PK\x03\x04"
MAGIC_EXE = b"MZ"
MAGIC_ELF = b"\x7fELF"
MAGIC_PNG = b"\x89PNG\r\n\x1a\n"
MAGIC_JPEG = b"\xff\xd8\xff"


def detect_file_signature(path: Path) -> Tuple[Optional[str], bytes]:
    """Inspect initial file header bytes to identify true file type."""
    try:
        with open(path, "rb") as f:
            header = f.read(2048)
    except Exception:
        return None, b""

    if header.startswith(MAGIC_PDF):
        return "pdf", header
    if header.startswith(MAGIC_ZIP):
        return "zip", header
    if header.startswith(MAGIC_EXE) or header.startswith(MAGIC_ELF):
        return "binary_executable", header
    if header.startswith(MAGIC_PNG) or header.startswith(MAGIC_JPEG):
        return "image", header

    # Test for plain text: no null bytes in header sample
    if b"\x00" not in header:
        return "txt", header

    return "unknown", header


def inspect_office_zip(
    path: Path, expected_type: str, config: IngestionConfig
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate DOCX/PPTX archive structure and defend against zip bombs."""
    try:
        with zipfile.ZipFile(path, "r") as zf:
            namelist = set(zf.namelist())

            # Check required Office XML members
            if "[Content_Types].xml" not in namelist:
                return False, "ERR_CORRUPT_FILE", "Archive lacks standard Office OpenXML manifest"

            if expected_type == "docx" and not any(n.startswith("word/") for n in namelist):
                return False, "ERR_FORMAT_MISMATCH", "Archive is not a valid DOCX document structure"

            if expected_type == "pptx" and not any(n.startswith("ppt/") for n in namelist):
                return False, "ERR_FORMAT_MISMATCH", "Archive is not a valid PPTX presentation structure"

            # Zip bomb defenses: measure compression ratio and uncompressed volume
            total_compressed = 0
            total_uncompressed = 0
            for info in zf.infolist():
                total_compressed += info.compress_size
                total_uncompressed += info.file_size

                if total_uncompressed > config.zip_bomb_max_uncompressed_bytes:
                    return (
                        False,
                        "ERR_ZIP_BOMB_DETECTED",
                        "Uncompressed archive size exceeds maximum safety limit",
                    )

            effective_compressed = max(1, total_compressed)
            ratio = total_uncompressed / effective_compressed
            if ratio > config.zip_bomb_max_ratio and total_uncompressed > 10 * 1024 * 1024:
                return (
                    False,
                    "ERR_ZIP_BOMB_DETECTED",
                    "Archive compression ratio exceeds safe limit",
                )

            return True, None, None

    except zipfile.BadZipFile:
        return False, "ERR_CORRUPT_FILE", "File is corrupted or not a valid zip archive"
    except Exception as e:
        return False, "ERR_VALIDATION_FAILED", "Failed inspecting archive structure"


def validate_file(file_path: str, config: Optional[IngestionConfig] = None) -> ValidationResult:
    """Perform pre-flight security and sanity validation on the target file.

    Guarantees: Never raises an exception; always returns a ValidationResult.
    """
    if not file_path or not isinstance(file_path, (str, Path)):
        return ValidationResult(
            is_valid=False,
            error_code="ERR_INVALID_FILE_PATH",
            error_message="Specified file path is empty or invalid",
        )
    cfg = config or IngestionConfig()
    try:
        path = Path(file_path)
    except Exception:
        return ValidationResult(
            is_valid=False,
            error_code="ERR_INVALID_FILE_PATH",
            error_message="Specified file path cannot be resolved as a valid path",
        )

    # 1. Existence and file type
    if not path.exists():
        return ValidationResult(
            is_valid=False,
            error_code="ERR_FILE_NOT_FOUND",
            error_message="Specified file path does not exist",
        )

    if not path.is_file():
        return ValidationResult(
            is_valid=False,
            error_code="ERR_NOT_A_FILE",
            error_message="Specified path is a directory or special device",
        )

    # 2. Size limits (Empty & Oversized)
    try:
        size = path.stat().st_size
    except Exception:
        return ValidationResult(
            is_valid=False,
            error_code="ERR_CANNOT_STAT_FILE",
            error_message="Could not read file attributes",
        )

    if size == 0:
        return ValidationResult(
            is_valid=False,
            error_code="ERR_EMPTY_FILE",
            error_message="File is empty (0 bytes)",
        )

    if size > cfg.max_file_size_bytes:
        return ValidationResult(
            is_valid=False,
            error_code="ERR_FILE_OVERSIZED",
            error_message="File exceeds maximum allowed size limit",
        )

    # 3. Extension vs True Magic Byte Signature
    ext = path.suffix.lower().lstrip(".")
    sig_type, header = detect_file_signature(path)

    # Disallow known executables immediately
    if sig_type == "binary_executable":
        return ValidationResult(
            is_valid=False,
            error_code="ERR_RENAMED_EXECUTABLE",
            error_message="File signature indicates an executable binary",
        )

    # Validate PDF
    if ext == "pdf":
        if sig_type != "pdf":
            return ValidationResult(
                is_valid=False,
                error_code="ERR_SIGNATURE_MISMATCH",
                error_message="File extension is PDF but header signature does not match PDF format",
            )
        # Check if PDF is encrypted or corrupt via lightweight check
        try:
            try:
                import pymupdf
                doc = pymupdf.open(str(path))
                if doc.is_encrypted:
                    doc.close()
                    return ValidationResult(
                        is_valid=False,
                        detected_format="pdf",
                        error_code="ERR_PASSWORD_PROTECTED",
                        error_message="PDF document is encrypted or password-protected",
                    )
                if len(doc) == 0:
                    doc.close()
                    return ValidationResult(
                        is_valid=False,
                        detected_format="pdf",
                        error_code="ERR_CORRUPT_FILE",
                        error_message="PDF document contains zero pages or is corrupted",
                    )
                doc.close()
            except ImportError:
                import pypdf
                reader = pypdf.PdfReader(str(path))
                if reader.is_encrypted:
                    return ValidationResult(
                        is_valid=False,
                        detected_format="pdf",
                        error_code="ERR_PASSWORD_PROTECTED",
                        error_message="PDF document is encrypted or password-protected",
                    )
                if len(reader.pages) == 0:
                    return ValidationResult(
                        is_valid=False,
                        detected_format="pdf",
                        error_code="ERR_CORRUPT_FILE",
                        error_message="PDF document contains zero pages or is corrupted",
                    )
        except Exception:
            return ValidationResult(
                is_valid=False,
                detected_format="pdf",
                error_code="ERR_CORRUPT_FILE",
                error_message="PDF file structure is malformed or corrupted",
            )
        return ValidationResult(is_valid=True, detected_format="pdf")

    # Validate DOCX
    elif ext == "docx":
        if sig_type != "zip":
            return ValidationResult(
                is_valid=False,
                error_code="ERR_SIGNATURE_MISMATCH",
                error_message="File extension is DOCX but header signature does not match zip container",
            )
        ok, code, msg = inspect_office_zip(path, "docx", cfg)
        if not ok:
            return ValidationResult(
                is_valid=False, detected_format="docx", error_code=code, error_message=msg
            )
        return ValidationResult(is_valid=True, detected_format="docx")

    # Validate PPTX
    elif ext == "pptx":
        if sig_type != "zip":
            return ValidationResult(
                is_valid=False,
                error_code="ERR_SIGNATURE_MISMATCH",
                error_message="File extension is PPTX but header signature does not match zip container",
            )
        ok, code, msg = inspect_office_zip(path, "pptx", cfg)
        if not ok:
            return ValidationResult(
                is_valid=False, detected_format="pptx", error_code=code, error_message=msg
            )
        return ValidationResult(is_valid=True, detected_format="pptx")

    # Validate TXT
    elif ext in ("txt", "text", "log"):
        if sig_type != "txt":
            return ValidationResult(
                is_valid=False,
                error_code="ERR_SIGNATURE_MISMATCH",
                error_message="File contains binary bytes incompatible with text format",
            )
        return ValidationResult(is_valid=True, detected_format="txt")

    # Unsupported format
    else:
        return ValidationResult(
            is_valid=False,
            error_code="ERR_UNSUPPORTED_FORMAT",
            error_message="File extension is not supported by ingestion pipeline",
        )
