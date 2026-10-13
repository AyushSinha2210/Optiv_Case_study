"""SLA calculation, reminder dispatch, and automated reassessment scheduler.

Source Authority: Cadence_TPRM_Training.docx Section 2.3, Appendix A (AR.T1.1, AR.T2.1, AR.T3.1), Appendix D (Table 13).
"""

from typing import List, Dict
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from src.cadence_tprm.models.vendor import Vendor
from src.cadence_tprm.models.assessment import Assessment, QuestionResponse
from src.cadence_tprm.models.task import Task, Notification
from src.cadence_tprm.services.audit_service import AuditService

class SLAService:

    @staticmethod
    def run_daily_reassessment_automation(db: Session, actor_email: str = "system@cadence.com") -> Dict[str, int]:
        """Executes Appendix A automation rules:

        - AR.T1.1: Tier 1 Reassessment (Days >= 275)
        - AR.T2.1: Tier 2 Reassessment (Days >= 640)
        - AR.T3.1: Tier 3 Reassessment (Days >= 640)
        """
        now = datetime.now(timezone.utc)
        results = {"tier1_reassessments": 0, "tier2_reassessments": 0, "tier3_reassessments": 0}

        # Query active Live vendors with prior assessment completion dates
        live_vendors = db.query(Vendor).filter(
            Vendor.lifecycle_status == "Live",
            Vendor.last_assessment_completion_date.isnot(None)
        ).all()

        for vendor in live_vendors:
            days_since = (now - vendor.last_assessment_completion_date.replace(tzinfo=timezone.utc)).days

            should_trigger = False
            template_code = "T1-2_v1"
            rule_id = ""

            if vendor.vendor_tier == "Tier 1" and days_since >= 275:
                should_trigger = True
                template_code = "T1-2_v1"
                rule_id = "AR.T1.1"
                results["tier1_reassessments"] += 1
            elif vendor.vendor_tier == "Tier 2" and days_since >= 640:
                should_trigger = True
                template_code = "T1-2_v1"
                rule_id = "AR.T2.1"
                results["tier2_reassessments"] += 1
            elif vendor.vendor_tier == "Tier 3" and days_since >= 640:
                should_trigger = True
                template_code = "T3_v1"
                rule_id = "AR.T3.1"
                results["tier3_reassessments"] += 1

            if should_trigger:
                # Check if a pending reassessment already exists to ensure idempotency
                existing_pending = db.query(Assessment).filter(
                    Assessment.vendor_id == vendor.id,
                    Assessment.status.in_(["Draft", "Submitted", "In Review"])
                ).first()

                if existing_pending:
                    continue  # Already in flight

                # Find previous assessment to copy responses
                prev_asm = db.query(Assessment).filter_by(
                    vendor_id=vendor.id, status="Approved"
                ).order_by(Assessment.completed_at.desc()).first()

                # Create new reassessment
                new_asm = Assessment(
                    vendor_id=vendor.id,
                    template_code=template_code,
                    respondent_email=vendor.primary_vendor_contact,
                    approver_group="Vendor Risk Management Group",
                    status="Draft",
                    due_date=now + timedelta(days=9)  # SLA.1
                )
                db.add(new_asm)
                db.flush()

                # Action: Copy Previous Assessment = Yes
                if prev_asm:
                    for resp in prev_asm.responses:
                        db.add(QuestionResponse(
                            assessment_id=new_asm.id,
                            question_code=resp.question_code,
                            response_value=resp.response_value
                        ))

                # Update vendor stage to Launching reassessment
                vendor.current_stage = f"Reassessment {vendor.vendor_tier}"
                vendor.lifecycle_status = "In Progress"

                # Send email/notification to Business Owner: "Vendor Upcoming Re-Assessment"
                db.add(Notification(
                    recipient_email=vendor.business_owner,
                    subject=f"Vendor Upcoming Re-Assessment: {vendor.name}",
                    body=f"Annual/Bi-annual reassessment rule {rule_id} triggered for '{vendor.name}'. Reassessment questionnaire dispatched.",
                    notification_type="InApp"
                ))

                # Send assessment link to Primary Vendor Contact
                db.add(Notification(
                    recipient_email=vendor.primary_vendor_contact,
                    subject=f"Cadence Re-Assessment Due: {vendor.name}",
                    body=f"Your periodic reassessment ({template_code}) has been launched with previous answers pre-populated. Please verify and submit.",
                    notification_type="InApp",
                    link_url=f"/assessments/{new_asm.id}"
                ))

                AuditService.log_event(
                    db,
                    actor_email=actor_email,
                    action="REASSESSMENT_LAUNCHED",
                    entity_type="VENDOR",
                    entity_id=vendor.id,
                    details={
                        "rule_id": rule_id,
                        "days_since_completion": days_since,
                        "assessment_id": new_asm.id
                    }
                )

        db.commit()
        return results

    @staticmethod
    def process_sla_reminders(db: Session) -> int:
        """Evaluates pending tasks and issues SLA reminders when reminder dates pass."""
        now = datetime.now(timezone.utc)
        pending_tasks = db.query(Task).filter(
            Task.status == "Pending",
            Task.reminder_sent == False,
            Task.reminder_date.isnot(None),
            Task.reminder_date <= now
        ).all()

        reminders_sent = 0
        for task in pending_tasks:
            recipient = task.assignee_email or "daniela.figueroa@cadence.com"
            db.add(Notification(
                recipient_email=recipient,
                subject=f"SLA REMINDER: {task.title}",
                body=f"Task '{task.title}' is due on {task.due_date.strftime('%Y-%m-%d')}. Please action immediately.",
                notification_type="InApp"
            ))
            task.reminder_sent = True
            reminders_sent += 1

        db.commit()
        return reminders_sent
