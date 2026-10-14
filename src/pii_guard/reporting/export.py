"""Sanitized report export module for JSON and CSV formats.

PRIVACY MANDATE:
All export formats are constrained by an explicit field allowlist.
No raw document content, unredacted text, or sensitive customer details can be exported.
"""

import csv
import io
import json
from pathlib import Path
from typing import List, Optional, Union

from ..orchestration.models import ProcessingReport


def export_to_json(
    report: ProcessingReport, output_path: Optional[Union[str, Path]] = None, indent: int = 2
) -> str:
    """Export ProcessingReport to sanitized Contract D JSON string, optionally writing to disk."""
    data = report.model_dump(mode="json")
    json_str = json.dumps(data, indent=indent)

    if output_path is not None:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json_str, encoding="utf-8")

    return json_str


def export_to_csv(
    reports: List[ProcessingReport], output_path: Optional[Union[str, Path]] = None
) -> str:
    """Export a collection of reports to CSV with strictly allowlisted metadata columns."""
    output = io.StringIO()
    fieldnames = [
        "document_id",
        "workflow_status",
        "verification_status",
        "release_allowed",
        "precision",
        "recall",
        "f1_score",
        "false_negative_rate",
        "created_at",
        "processing_duration_sec",
        "total_entities",
        "category_counts_json",
        "warnings_count",
        "safe_error",
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()

    for rep in reports:
        total_ents = sum(rep.category_counts.values()) if rep.category_counts else 0
        row = {
            "document_id": rep.document_id,
            "workflow_status": rep.workflow_status,
            "verification_status": rep.verification_status,
            "release_allowed": rep.release_allowed,
            "precision": round(getattr(rep, "precision", 1.0), 4),
            "recall": round(getattr(rep, "recall", 1.0), 4),
            "f1_score": round(getattr(rep, "f1_score", 1.0), 4),
            "false_negative_rate": round(getattr(rep, "false_negative_rate", 0.0), 4),
            "created_at": rep.created_at.isoformat(),
            "processing_duration_sec": rep.processing_duration_sec,
            "total_entities": total_ents,
            "category_counts_json": json.dumps(rep.category_counts),
            "warnings_count": len(rep.safe_warnings),
            "safe_error": rep.safe_error or "",
        }
        writer.writerow(row)

    csv_str = output.getvalue()

    if output_path is not None:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(csv_str, encoding="utf-8")

    return csv_str
