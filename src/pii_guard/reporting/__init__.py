"""PII Guard Reporting & Audit Subsystem.

Owned by Member 5 (Tirth) and Member 4 (Nancy).
Provides sanitized audit logging, structured report generation, evaluation metrics, and zero-leakage exports.
"""

from .audit import AuditEvent, AuditTrail, get_global_audit_trail
from .report_generator import generate_report, generate_human_readable_summary
from .metrics import calculate_evaluation_metrics, DetectionMetricResult, MatchingStrategy, EntityAnnotation
from .export import export_to_json, export_to_csv

__all__ = [
    "AuditEvent",
    "AuditTrail",
    "get_global_audit_trail",
    "generate_report",
    "generate_human_readable_summary",
    "calculate_evaluation_metrics",
    "DetectionMetricResult",
    "MatchingStrategy",
    "EntityAnnotation",
    "export_to_json",
    "export_to_csv",
]
