"""Structured report generator producing Contract D audit and executive summaries.

PRIVACY MANDATE:
Reports strictly contain metadata, stage outcomes, entity category counts,
and authorization decisions. They NEVER contain raw document text or PII values.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any

from ..orchestration.models import ProcessingResult, ProcessingReport


def generate_report(result: ProcessingResult) -> ProcessingReport:
    """Transform ProcessingResult into canonical Contract D ProcessingReport."""
    duration = 0.0
    if result.completed_at and result.started_at:
        duration = (result.completed_at - result.started_at).total_seconds()
        if duration < 0:
            duration = 0.0

    return ProcessingReport(
        document_id=result.document_id,
        workflow_status=result.workflow_status,
        category_counts=dict(result.category_counts),
        verification_status=result.verification_status or "INCOMPLETE",
        release_allowed=bool(result.release_allowed),
        created_at=datetime.now(timezone.utc),
        processing_duration_sec=round(duration, 4),
        module_versions={
            "ingestion": "1.0.0",
            "detection": "1.0.0",
            "redaction": "1.0.0",
            "orchestration": "1.0.0",
        },
        safe_warnings=list(result.safe_warnings),
        safe_error=result.safe_error,
    )


def generate_human_readable_summary(report: ProcessingReport) -> str:
    """Produce a clear, privacy-safe executive text report for the UI and CLI."""
    lines = [
        "=" * 72,
        "CADENCE FINANCIAL GROUP — PII PROTECTION PIPELINE REPORT",
        "=" * 72,
        f"Document ID:         {report.document_id}",
        f"Generated At (UTC):   {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Processing Duration: {report.processing_duration_sec:.3f} seconds",
        "-" * 72,
        f"Workflow Outcome:    {report.workflow_status.upper()}",
        f"Verification Gate:   {report.verification_status}",
        f"Release Decision:    {'AUTHORIZED FOR RELEASE' if report.release_allowed else 'RELEASE BLOCKED / WITHHELD'}",
        "-" * 72,
        "PII Category Breakdown (Entity Counts):",
    ]

    if report.category_counts:
        for cat, count in sorted(report.category_counts.items()):
            lines.append(f"  - {cat:<24}: {count}")
        total = sum(report.category_counts.values())
        lines.append(f"  Total Entities Detected: {total}")
    else:
        lines.append("  (No PII entities detected or stage did not run)")

    if report.safe_warnings:
        lines.append("-" * 72)
        lines.append("Processing Warnings:")
        for w in report.safe_warnings:
            lines.append(f"  * {w}")

    if report.safe_error:
        lines.append("-" * 72)
        lines.append(f"Processing Error Note: {report.safe_error}")

    lines.append("-" * 72)
    lines.append("Module Versions:")
    for mod, ver in sorted(report.module_versions.items()):
        lines.append(f"  - {mod:<16}: v{ver}")

    lines.append("=" * 72)
    lines.append("PRIVACY NOTICE: In compliance with Cadence AI Governance, this report")
    lines.append("contains exclusively sanitized operational metadata. No raw document")
    lines.append("text, customer information, or detected PII values are retained.")
    lines.append("=" * 72)

    return "\n".join(lines)
