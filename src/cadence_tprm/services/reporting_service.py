"""Executive Reporting & Operational Metrics Service.

Computes authoritative indicators directly from persistent database records with zero fabricated data.
"""

from typing import Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.cadence_tprm.models.vendor import Vendor
from src.cadence_tprm.models.assessment import Assessment, RiskFinding
from src.cadence_tprm.models.task import Task

class ReportingService:

    @staticmethod
    def get_dashboard_summary(db: Session) -> Dict[str, Any]:
        """Calculates executive dashboard metrics from actual relational rows."""
        now = datetime.now(timezone.utc)

        # 1. Total vendors & Breakdown
        total_vendors = db.query(Vendor).count()

        # Category breakdown
        cat_counts = (
            db.query(Vendor.vendor_category, func.count(Vendor.id))
            .group_by(Vendor.vendor_category)
            .all()
        )
        vendors_by_category = {cat: count for cat, count in cat_counts}

        # Tier breakdown
        tier_counts = (
            db.query(Vendor.vendor_tier, func.count(Vendor.id))
            .group_by(Vendor.vendor_tier)
            .all()
        )
        vendors_by_tier = {tier: count for tier, count in tier_counts}

        # Status breakdown
        status_counts = (
            db.query(Vendor.lifecycle_status, func.count(Vendor.id))
            .group_by(Vendor.lifecycle_status)
            .all()
        )
        vendors_by_status = {st: count for st, count in status_counts}

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

        # 5. Upcoming reassessments
        reassessments_due = db.query(Vendor).filter(
            Vendor.lifecycle_status == "Live",
            Vendor.next_reassessment_due_date.isnot(None),
            Vendor.next_reassessment_due_date <= (now + func.datetime('now', '+90 days'))
        ).count()

        return {
            "total_vendors": total_vendors,
            "vendors_by_category": vendors_by_category,
            "vendors_by_tier": vendors_by_tier,
            "vendors_by_status": vendors_by_status,
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
            }
        }
