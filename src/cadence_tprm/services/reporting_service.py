"""Executive Reporting, Operational Metrics, and Authorized Export Service.

Computes authoritative indicators directly from persistent database records with zero fabricated data.
Source Authority: Cadence_TPRM_Training.docx Section 23, 24.
"""

import csv
import io
import json
from typing import Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.cadence_tprm.models.vendor import Vendor, Contract, RenewalDecision
from src.cadence_tprm.models.assessment import Assessment, RiskFinding
from src.cadence_tprm.models.task import Task
from src.cadence_tprm.models.audit import AuditLog
from src.cadence_tprm.services.audit_service import AuditService

class ReportingService:

    @staticmethod
    def get_dashboard_summary(db: Session) -> Dict[str, Any]:
        """Calculates executive dashboard metrics from actual relational rows."""
        now = datetime.now(timezone.utc)

        # 1. Total vendors & Breakdown
        total_vendors = db.query(Vendor).count()

        cat_counts = (
            db.query(Vendor.vendor_category, func.count(Vendor.id))
            .group_by(Vendor.vendor_category)
            .all()
        )
        vendors_by_category = {cat: count for cat, count in cat_counts}

        tier_counts = (
            db.query(Vendor.vendor_tier, func.count(Vendor.id))
            .group_by(Vendor.vendor_tier)
            .all()
        )
        vendors_by_tier = {tier: count for tier, count in tier_counts}

        status_counts = (
            db.query(Vendor.lifecycle_status, func.count(Vendor.id))
            .group_by(Vendor.lifecycle_status)
            .all()
        )
        vendors_by_status = {st: count for st, count in status_counts}

        stage_counts = (
            db.query(Vendor.current_stage, func.count(Vendor.id))
            .group_by(Vendor.current_stage)
            .all()
        )
        vendors_by_stage = {stg: count for stg, count in stage_counts}

        # 2. Assessments summary
        total_assessments = db.query(Assessment).count()
        pending_assessments = db.query(Assessment).filter(Assessment.status.in_(["Draft", "Submitted", "In Review"])).count()
        approved_assessments = db.query(Assessment).filter(Assessment.status == "Approved").count()
        rejected_assessments = db.query(Assessment).filter(Assessment.status == "Rejected").count()

        # 3. Risk findings summary
        total_findings = db.query(RiskFinding).count()
        open_findings = db.query(RiskFinding).filter(RiskFinding.status == "Open").count()
        high_risks = db.query(RiskFinding).filter(RiskFinding.inherent_risk == "High", RiskFinding.status == "Open").count()
        medium_risks = db.query(RiskFinding).filter(RiskFinding.inherent_risk == "Medium", RiskFinding.status == "Open").count()
        low_risks = db.query(RiskFinding).filter(RiskFinding.inherent_risk == "Low", RiskFinding.status == "Open").count()

        # 4. Tasks and SLA compliance
        pending_tasks = db.query(Task).filter(Task.status == "Pending").count()
        overdue_tasks = db.query(Task).filter(Task.status == "Pending", Task.due_date < now).count()

        # 5. Upcoming reassessments (fixed Python timedelta calculation)
        horizon_90d = now + timedelta(days=90)
        reassessments_due = db.query(Vendor).filter(
            Vendor.lifecycle_status == "Live",
            Vendor.next_reassessment_due_date.isnot(None),
            Vendor.next_reassessment_due_date <= horizon_90d
        ).count()

        renewals_pending = db.query(RenewalDecision).filter(
            RenewalDecision.decision.in_(["Pending", "Pending Reassessment"])
        ).count()

        return {
            "total_vendors": total_vendors,
            "vendors_by_category": vendors_by_category,
            "vendors_by_tier": vendors_by_tier,
            "vendors_by_status": vendors_by_status,
            "vendors_by_stage": vendors_by_stage,
            "assessments": {
                "total": total_assessments,
                "pending": pending_assessments,
                "approved": approved_assessments,
                "rejected": rejected_assessments,
            },
            "risk_findings": {
                "total": total_findings,
                "open": open_findings,
                "high": high_risks,
                "medium": medium_risks,
                "low": low_risks,
            },
            "sla_and_tasks": {
                "pending_tasks": pending_tasks,
                "overdue_tasks": overdue_tasks,
                "reassessments_due": reassessments_due,
                "renewals_pending": renewals_pending,
            }
        }

    @staticmethod
    def export_report_csv(db: Session, report_type: str, actor_email: str) -> str:
        """Generates a real CSV export from actual database records and logs an export audit event."""
        buf = io.StringIO()
        writer = csv.writer(buf)

        if report_type == "vendors":
            writer.writerow(["ID", "Name", "Category", "Tier", "Type", "Criticality", "Lifecycle Status", "Workflow", "Stage", "Primary Contact", "Business Owner", "Next Reassessment"])
            for v in db.query(Vendor).order_by(Vendor.name.asc()).all():
                writer.writerow([
                    v.id, v.name, v.vendor_category, v.vendor_tier, v.type, v.criticality,
                    v.lifecycle_status, v.current_workflow_name, v.current_stage,
                    v.primary_vendor_contact, v.business_owner,
                    v.next_reassessment_due_date.isoformat() if v.next_reassessment_due_date else ""
                ])
        elif report_type == "findings":
            writer.writerow(["ID", "Rule Code", "Risk Name", "Inherent Risk", "Control ID", "Control Name", "Responsible Group", "Status", "Due Date", "Mitigation Recommendation"])
            for f in db.query(RiskFinding).order_by(RiskFinding.rule_code.asc()).all():
                writer.writerow([
                    f.id, f.rule_code, f.risk_name, f.inherent_risk, f.control_id, f.control_name,
                    f.responsible_group, f.status,
                    f.due_date.isoformat() if f.due_date else "",
                    f.mitigation_recommendation or ""
                ])
        elif report_type == "assessments":
            writer.writerow(["ID", "Vendor ID", "Template Code", "Status", "Overall Score", "Respondent", "Approver Group", "Due Date", "Completed At", "Decision By"])
            for a in db.query(Assessment).order_by(Assessment.created_at.desc()).all():
                writer.writerow([
                    a.id, a.vendor_id, a.template_code, a.status, a.overall_score,
                    a.respondent_email, a.approver_group,
                    a.due_date.isoformat() if a.due_date else "",
                    a.completed_at.isoformat() if a.completed_at else "",
                    a.decision_by or ""
                ])
        else:
            writer.writerow(["ID", "Timestamp", "Actor Email", "Action", "Entity Type", "Entity ID", "Details"])
            for l in db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(250).all():
                writer.writerow([
                    l.id, l.timestamp.isoformat(), l.actor_email, l.action, l.entity_type, l.entity_id, json.dumps(l.details)
                ])

        AuditService.log_event(
            db,
            actor_email=actor_email,
            action="REPORT_EXPORTED",
            entity_type="REPORT",
            entity_id=report_type,
            details={"report_type": report_type, "format": "CSV"}
        )
        return buf.getvalue()
