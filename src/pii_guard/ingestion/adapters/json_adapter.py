"""JSON adapter for document privacy ingestion and extraction."""

import json
from pathlib import Path
from typing import List, Any

from .base import BaseAdapter, AdapterPage, AdapterResult
from ..config import IngestionConfig
from ..schemas import WarningInfo


def _format_json_node(key_path: str, value: Any, lines: List[str]) -> None:
    """Format JSON keys and values into an accessible, traceable text representation."""
    if isinstance(value, dict):
        for k, v in value.items():
            new_path = f"{key_path}.{k}" if key_path else str(k)
            _format_json_node(new_path, v, lines)
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            new_path = f"{key_path}[{idx}]"
            _format_json_node(new_path, item, lines)
    else:
        str_val = str(value) if value is not None else "null"
        if key_path:
            lines.append(f"{key_path}: {str_val}")
        else:
            lines.append(str_val)


class JSONAdapter(BaseAdapter):
    """Adapter for structured JSON files preserving key hierarchy and string values."""

    def extract(self, path: Path, config: IngestionConfig) -> AdapterResult:
        warnings: List[WarningInfo] = []
        try:
            raw_text = path.read_text(encoding="utf-8", errors="replace")
            data = json.loads(raw_text)
        except Exception as e:
            return AdapterResult(
                pages=[],
                warnings=[
                    WarningInfo(
                        code="ERR_CORRUPT_FILE",
                        message=f"JSON parsing error: malformed structure",
                    )
                ],
                source_type="json",
            )

        lines: List[str] = []
        _format_json_node("", data, lines)
        extracted_text = "\n".join(lines).strip()
        if not extracted_text:
            extracted_text = "{}"

        page = AdapterPage(
            page_num=1,
            label="page",
            text=extracted_text,
            method="native",
            ocr_confidence=None,
            warnings=[],
        )

        return AdapterResult(
            pages=[page],
            warnings=warnings,
            source_type="json",
        )
