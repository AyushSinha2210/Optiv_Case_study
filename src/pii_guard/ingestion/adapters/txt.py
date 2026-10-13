"""Plain text (TXT) adapter with encoding sniffing and replacement character detection."""

from pathlib import Path
from typing import List

from .base import BaseAdapter, AdapterPage, AdapterResult
from ..config import IngestionConfig
from ..schemas import WarningInfo


class TXTAdapter(BaseAdapter):
    """Robust text extractor prioritizing UTF-8 and standard Western encodings with charset-normalizer fallback."""

    def extract(self, path: Path, config: IngestionConfig) -> AdapterResult:
        warnings: List[WarningInfo] = []
        raw_bytes = path.read_bytes()
        text = ""
        used_encoding = "utf-8"

        # 1. Fast-path: Strict UTF-8 decode
        try:
            text = raw_bytes.decode("utf-8")
            used_encoding = "utf-8"
        except UnicodeDecodeError:
            # 2. Try Windows-1252 / ISO-8859-1 (standard for Western financial systems)
            try:
                text = raw_bytes.decode("cp1252")
                used_encoding = "cp1252"
            except UnicodeDecodeError:
                # 3. Use charset-normalizer for arbitrary international encodings
                detected_text = None
                try:
                    import charset_normalizer
                    detected = charset_normalizer.from_bytes(raw_bytes).best()
                    if detected is not None and detected.encoding:
                        detected_text = str(detected)
                        used_encoding = detected.encoding
                except ImportError:
                    pass

                if detected_text is not None:
                    text = detected_text
                else:
                    # 4. Safe fallback
                    text = raw_bytes.decode("latin-1", errors="replace")
                    used_encoding = "latin-1"

        # Check for replacement characters
        if "\ufffd" in text:
            warnings.append(
                WarningInfo(
                    code="WARN_ENCODING_REPLACEMENT_CHAR",
                    page=1,
                    message="Detected unicode replacement characters (U+FFFD) during text decoding",
                )
            )

        pages = [
            AdapterPage(
                page_num=1,
                label="page",
                text=text.strip(),
                method="native",
                ocr_confidence=None,
                warnings=[],
            )
        ]

        return AdapterResult(pages=pages, warnings=warnings, source_type="txt")
