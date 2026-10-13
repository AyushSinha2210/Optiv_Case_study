"""Authoritative Workflow Finite State Machine (FSM) Engine.

Source Authority: Cadence_TPRM_Training.docx Section 4.2, 5.1, 6.4, Appendix A, Tables 6, 7, 8, 10.
"""

from typing import Dict, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.cadence_tprm.models.vendor import Vendor
from src.cadence_tprm.models.assessment import Assessment
from src.cadence_tprm.models.workflow import Workflow, WorkflowInstance, WorkflowTransition
from src.cadence_tprm.models.task import Task, Notification
from src.cadence_tprm.services.audit_service import AuditService

# Authoritative mapping of Workflow Name -> (Prefix, Launch Stage, Reject Stage, Approve Rule, Reject Rule, Reject Notify Rule, Approve Notify Rule)
WORKFLOW_METADATA: Dict[str, Tuple[str, str, str, str, str, str, str]] = {
    "CD_Revenue Partners Workflow": ("RP", "Launching RevPart", "Review Reject RevPart", "WR.RP.3", "PWR.RP.4", "WR.RP.5", "WR.RP.6"),
    "CD_Marketing Partners Workflow": ("MP", "Launching MarPart", "Review Reject MarPart", "WR.MP.3", "WR.MP.4", "WR.MP.5", "WR.MP.6"),
    "CD_International Vendors Workflow": ("IV", "Launching IntVen", "Review Reject IntVen", "WR.IV.3", "WR.IV.4", "WR.IV.5", "WR.IV.6"),
    "CD_Service Providers Workflow": ("SP", "Launching ServPro", "Review Reject ServPro", "WR.SP.3", "WR.SP.4", "WR.SP.5", "WR.SP.6"),
    "CD_Staffing Vendors Workflow": ("SV", "Launching StafVen", "Review Reject StafVen", "WR.SV.3", "WR.SV.4", "WR.SV.5", "WR.SV.6"),
    "CD_Tier3 Workflow": ("T3", "Launching Tier3", "Review Reject Tier3", "WR.T3.3", "WR.T3.4", "WR.T3.5", "WR.T3.6"),
}

class WorkflowEngine:

    @staticmethod
    def route_new_vendor(db: Session, vendor: Vendor, actor_email: str) -> str:
        """Evaluates Onboarding stage rules WR.ON.1 to WR.ON.6 and category push rules WR.*.1.

        Routes vendor from CD_Onboarding Workflow ('New Third Party') to the target tier/category workflow.
        """
        tier = vendor.vendor_tier
        category = vendor.vendor_category

        if tier == "Tier 3":
            # WR.ON.6: Tier 3 rule takes precedence across all categories
            target_workflow = "CD_Tier3 Workflow"
            launch_stage = "Launching Tier3"
            on_rule = "WR.ON.6"
            push_rule = "WR.T3.1"
            launch_rule = "WR.T3.2"
        elif category == "Revenue Partner" and tier in ["Tier 1", "Tier 2"]:
            target_workflow = "CD_Revenue Partners Workflow"
            launch_stage = "Launching RevPart"
            on_rule = "WR.ON.1"
            push_rule = "WR.RP.1"
            launch_rule = "WR.RP.2"
        elif category == "Marketing Partner" and tier in ["Tier 1", "Tier 2"]:
            target_workflow = "CD_Marketing Partners Workflow"
            launch_stage = "Launching MarPart"
            on_rule = "WR.ON.2"
            push_rule = "WR.MP.1"
            launch_rule = "WR.MP.2"
        elif category in ["International Vendor", "International Vendors"] and tier in ["Tier 1", "Tier 2"]:
            target_workflow = "CD_International Vendors Workflow"
            launch_stage = "Launching IntVen"
            on_rule = "WR.ON.3"
            push_rule = "WR.IV.1"
            launch_rule = "WR.IV.2"
        elif category in ["Service Provider and Vendor", "Service Providers and Vendors"] and tier in ["Tier 1", "Tier 2"]:
            target_workflow = "CD_Service Providers Workflow"
            launch_stage = "Launching ServPro"
            on_rule = "WR.ON.4"
            push_rule = "WR.SP.1"
            launch_rule = "WR.SP.2"
        elif category in ["Staffing Vendor", "Staffing Vendors"] and tier in ["Tier 1", "Tier 2"]:
            target_workflow = "CD_Staffing Vendors Workflow"
            launch_stage = "Launching StafVen"
            on_rule = "WR.ON.5"
            push_rule = "WR.SV.1"
            launch_rule = "WR.SV.2"
        else:
            target_workflow = "CD_Service Providers Workflow"
            launch_stage = "Launching ServPro"
            on_rule = "WR.ON.4"
            push_rule = "WR.SP.1"
            launch_rule = "WR.SP.2"

        old_stage = vendor.current_stage
        vendor.current_workflow_name = target_workflow
        vendor.current_stage = launch_stage
        vendor.lifecycle_status = "In Progress"

        wf_record = db.query(Workflow).filter_by(name=target_workflow).first()
        wf_id = wf_record.id if wf_record else None

        wf_instance = WorkflowInstance(
            workflow_id=wf_id,
            vendor_id=vendor.id,
            current_stage=launch_stage,
            started_at=datetime.now(timezone.utc)
        )
        db.add(wf_instance)
        db.flush()

        # Record Onboarding -> Category Workflow transition (WR.ON.1-6 & WR.*.1)
        db.add(WorkflowTransition(
            instance_id=wf_instance.id,
            actor_email=actor_email,
            from_stage=old_stage,
            to_stage=launch_stage,
            trigger_name="On_T_Assign Workflow",
            rule_name=f"{on_rule} -> {push_rule} -> {launch_rule}",
            decision_reason=f"Routed from CD_Onboarding Workflow ('{old_stage}') to '{target_workflow}' ('{launch_stage}') for Category='{category}', Tier='{tier}'."
        ))

        # Launch assessment per WR.*.2 or WR.T3.2 (SLA.1 = 9 days, reminder = 5 days)
        template_code = "T3_v1" if tier == "Tier 3" else "T1-2_v1"
        now = datetime.now(timezone.utc)
        assessment = Assessment(
            vendor_id=vendor.id,
            template_code=template_code,
            respondent_email=vendor.primary_vendor_contact,
            approver_group="Vendor Risk Management Group",
            status="Draft",
            due_date=now + timedelta(days=9),  # SLA.1 (9 days)
        )
        db.add(assessment)
        db.flush()

        # Create SLA.1 Assessment Completion tracking task for Primary Vendor Contact (9 days, reminder at 5 days)
        db.add(Task(
            vendor_id=vendor.id,
            assessment_id=assessment.id,
            task_type="Assessment Completion (SLA.1)",
            title=f"Complete Due Diligence Questionnaire ({template_code}): {vendor.name}",
            description=f"Stage Rule {launch_rule} / SLA.1: Complete and submit {template_code} within 9 days (reminder at 5 days).",
            assignee_email=vendor.primary_vendor_contact,
            collaborator_group="Vendor Risk Management Group",
            due_date=now + timedelta(days=9),
            reminder_date=now + timedelta(days=5),
            status="Pending",
        ))

        # Send launch notification to Primary Vendor Contact
        db.add(Notification(
            recipient_email=vendor.primary_vendor_contact,
            subject=f"Cadence Due Diligence Assessment Launched ({launch_rule}): {vendor.name}",
            body=f"Please complete the required Due Diligence Assessment ({template_code}) within 9 days (SLA.1).",
            notification_type="InApp",
            link_url=f"/assessments/{assessment.id}"
        ))

        # Send notification to Business Owner
        db.add(Notification(
            recipient_email=vendor.business_owner,
            subject=f"Vendor Onboarding Routed ({on_rule}): {vendor.name}",
            body=f"Vendor '{vendor.name}' classified as {tier} ({category}) and routed to {target_workflow} ({launch_stage}).",
            notification_type="InApp"
        ))

        AuditService.log_event(
            db,
            actor_email=actor_email,
            action="WORKFLOW_ROUTED",
            entity_type="VENDOR",
            entity_id=vendor.id,
            details={
                "target_workflow": target_workflow,
                "launch_stage": launch_stage,
                "onboarding_rule": on_rule,
                "push_rule": push_rule,
                "launch_rule": launch_rule,
                "assessment_id": assessment.id
            }
        )

        db.commit()
        return target_workflow

    @staticmethod
    def approve_vendor(db: Session, vendor: Vendor, assessment: Assessment, actor_email: str, reason: str):
        """Applies WR.*.3 (Approval transition to Live) and WR.*.6 (Approval notification)."""
        if vendor.lifecycle_status == "Live" and assessment.status == "Approved":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vendor assessment is already approved and in Live status.")

        wf_meta = WORKFLOW_METADATA.get(
            vendor.current_workflow_name,
            ("SP", "Launching ServPro", "Review Reject ServPro", "WR.SP.3", "WR.SP.4", "WR.SP.5", "WR.SP.6"),
        )
        prefix, _, _, approve_rule, _, _, notify_rule = wf_meta
        trigger_name = "T3_T_Assessment Auto-approve" if prefix == "T3" and actor_email == "system@cadence.com" else f"{prefix}_T_Assessment Approved"

        old_stage = vendor.current_stage
        now = datetime.now(timezone.utc)
        vendor.current_stage = "Live"
        vendor.lifecycle_status = "Live"
        vendor.last_assessment_completion_date = now

        # Calculate next reassessment due date per Section 2.3 & Appendix D (SLA.6 / SLA.7)
        reassessment_days = 365 if vendor.vendor_tier == "Tier 1" else 730
        vendor.next_reassessment_due_date = now + timedelta(days=reassessment_days)

        assessment.status = "Approved"
        assessment.completed_at = now
        assessment.decision_reason = reason
        assessment.decision_by = actor_email

        wf_inst = db.query(WorkflowInstance).filter_by(vendor_id=vendor.id).order_by(WorkflowInstance.started_at.desc()).first()
        if wf_inst:
            wf_inst.current_stage = "Live"
            db.add(WorkflowTransition(
                instance_id=wf_inst.id,
                actor_email=actor_email,
                from_stage=old_stage,
                to_stage="Live",
                trigger_name=trigger_name,
                rule_name=f"{approve_rule} / {notify_rule}",
                decision_reason=reason
            ))

        # Stage Rule WR.*.6: Notify approval
        db.add(Notification(
            recipient_email=vendor.business_owner,
            subject=f"Vendor Approved ({notify_rule}): {vendor.name}",
            body=f"Third-Party '{vendor.name}' has been approved and advanced to Live stage in {vendor.current_workflow_name}.",
            notification_type="InApp"
        ))
        db.add(Notification(
            recipient_email=vendor.primary_vendor_contact,
            subject=f"Cadence TPRM - Assessment Approved: {vendor.name}",
            body=f"Your due diligence assessment for '{vendor.name}' has been approved ({reason}).",
            notification_type="InApp"
        ))

        tasks = db.query(Task).filter_by(vendor_id=vendor.id, status="Pending").all()
        for t in tasks:
            if "Assessment" in t.task_type:
                t.status = "Completed"
                t.completed_at = now

        AuditService.log_event(
            db,
            actor_email=actor_email,
            action="VENDOR_APPROVED",
            entity_type="VENDOR",
            entity_id=vendor.id,
            details={
                "reason": reason,
                "previous_stage": old_stage,
                "new_stage": "Live",
                "workflow_rule": approve_rule,
                "stage_rule": notify_rule,
            }
        )

        db.commit()

    @staticmethod
    def reject_vendor(db: Session, vendor: Vendor, assessment: Assessment, actor_email: str, reason: str):
        """Applies WR.*.4 (Transition to exact Review Reject stage) and WR.*.5 (Notification & 14-day Business Owner task)."""
        wf_meta = WORKFLOW_METADATA.get(
            vendor.current_workflow_name,
            ("SP", "Launching ServPro", "Review Reject ServPro", "WR.SP.3", "WR.SP.4", "WR.SP.5", "WR.SP.6"),
        )
        prefix, _, reject_stage, _, reject_rule, notify_rule, _ = wf_meta
        trigger_name = f"{prefix}_T_Assessment Rejected"

        old_stage = vendor.current_stage
        now = datetime.now(timezone.utc)
        vendor.current_stage = reject_stage
        vendor.lifecycle_status = "Review Reject"

        assessment.status = "Rejected"
        assessment.completed_at = now
        assessment.decision_reason = reason
        assessment.decision_by = actor_email

        wf_inst = db.query(WorkflowInstance).filter_by(vendor_id=vendor.id).order_by(WorkflowInstance.started_at.desc()).first()
        if wf_inst:
            wf_inst.current_stage = reject_stage
            db.add(WorkflowTransition(
                instance_id=wf_inst.id,
                actor_email=actor_email,
                from_stage=old_stage,
                to_stage=reject_stage,
                trigger_name=trigger_name,
                rule_name=f"{reject_rule} / {notify_rule}",
                decision_reason=reason
            ))

        # Stage Rule WR.*.5: Send Notification AND Create Task (Assignee: Business Owner, Collaborator: VRM Team, Deadline: 14 Days)
        db.add(Notification(
            recipient_email=vendor.business_owner,
            subject=f"URGENT: Third-Party Rejected ({notify_rule}) - {vendor.name}",
            body=f"Vendor '{vendor.name}' advanced to '{reject_stage}'. Reason: {reason}. Action required within 14 days.",
            notification_type="InApp"
        ))

        db.add(Task(
            vendor_id=vendor.id,
            assessment_id=assessment.id,
            task_type="Review Reject Followup",
            title=f"Review Vendor Rejection ({notify_rule}): {vendor.name}",
            description=(
                f"Stage Rule {notify_rule} in '{reject_stage}': Follow up on vendor rejection. "
                f"Decision reason: {reason}. Coordinate remediation or offboarding within 14 days."
            ),
            assignee_email=vendor.business_owner,
            collaborator_group="Vendor Risk Management Group",
            due_date=now + timedelta(days=14),
            reminder_date=now + timedelta(days=7),
            status="Pending"
        ))

        AuditService.log_event(
            db,
            actor_email=actor_email,
            action="VENDOR_REJECTED",
            entity_type="VENDOR",
            entity_id=vendor.id,
            details={
                "reason": reason,
                "previous_stage": old_stage,
                "new_stage": reject_stage,
                "workflow_rule": reject_rule,
                "stage_rule": notify_rule,
            }
        )

        db.commit()

    @staticmethod
    def initiate_offboarding(db: Session, vendor: Vendor, actor_email: str, reason: str):
        """Transitions vendor to Offboarding review, notifies stakeholders, and creates offboarding tasks."""
        if vendor.lifecycle_status == "Closed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vendor is already Closed.")

        old_stage = vendor.current_stage
        now = datetime.now(timezone.utc)
        vendor.current_stage = "Offboarding Review"
        vendor.lifecycle_status = "Offboarding"

        wf_inst = db.query(WorkflowInstance).filter_by(vendor_id=vendor.id).order_by(WorkflowInstance.started_at.desc()).first()
        if wf_inst:
            wf_inst.current_stage = "Offboarding Review"
            db.add(WorkflowTransition(
                instance_id=wf_inst.id,
                actor_email=actor_email,
                from_stage=old_stage,
                to_stage="Offboarding Review",
                trigger_name="Offboarding Initiated",
                rule_name="OFFBOARDING_WORKFLOW",
                decision_reason=reason
            ))

        db.add(Notification(
            recipient_email=vendor.business_owner,
            subject=f"Offboarding Initiated: {vendor.name}",
            body=f"Offboarding workflow initiated for '{vendor.name}'. Stakeholder review and approval required prior to moving to Closed.",
            notification_type="InApp"
        ))

        db.add(Task(
            vendor_id=vendor.id,
            task_type="Offboarding Review & Approval",
            title=f"Offboarding Stakeholder Review & Deprovisioning: {vendor.name}",
            description=f"Review and approve offboarding actions, access revocation, and contract closure. Reason: {reason}.",
            assignee_email=actor_email,
            collaborator_group="Vendor Risk Management Group",
            due_date=now + timedelta(days=7),
            reminder_date=now + timedelta(days=3),
            status="Pending"
        ))

        AuditService.log_event(
            db,
            actor_email=actor_email,
            action="OFFBOARDING_INITIATED",
            entity_type="VENDOR",
            entity_id=vendor.id,
            details={"reason": reason, "previous_stage": old_stage, "new_stage": "Offboarding Review"}
        )

        db.commit()

    @staticmethod
    def close_vendor(db: Session, vendor: Vendor, actor_email: str, reason: str = "Offboarding completed; manually moved to Closed stage."):
        """Manually moves vendor to final Closed stage after offboarding completion (Section 4.2.2/4.2.3)."""
        old_stage = vendor.current_stage
        now = datetime.now(timezone.utc)
        vendor.current_stage = "Closed"
        vendor.lifecycle_status = "Closed"

        wf_inst = db.query(WorkflowInstance).filter_by(vendor_id=vendor.id).order_by(WorkflowInstance.started_at.desc()).first()
        if wf_inst:
            wf_inst.current_stage = "Closed"
            wf_inst.completed_at = now
            db.add(WorkflowTransition(
                instance_id=wf_inst.id,
                actor_email=actor_email,
                from_stage=old_stage,
                to_stage="Closed",
                trigger_name="Manual Move to Closed",
                rule_name="MANUAL_CLOSURE",
                decision_reason=reason
            ))

        # Complete pending offboarding tasks
        for t in db.query(Task).filter_by(vendor_id=vendor.id, status="Pending").all():
            if "Offboarding" in t.task_type:
                t.status = "Completed"
                t.completed_at = now

        AuditService.log_event(
            db,
            actor_email=actor_email,
            action="VENDOR_CLOSED",
            entity_type="VENDOR",
            entity_id=vendor.id,
            details={"previous_stage": old_stage, "new_stage": "Closed", "reason": reason}
        )
        db.commit()

    @staticmethod
    def archive_vendor(db: Session, vendor: Vendor, actor_email: str):
        """Manually archives a Closed vendor record (Section 4.2.2/4.2.3: never archive automatically)."""
        if vendor.lifecycle_status != "Closed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vendor must be in the 'Closed' stage before it can be manually archived."
            )
        vendor.is_archived = True
        AuditService.log_event(
            db,
            actor_email=actor_email,
            action="VENDOR_ARCHIVED",
            entity_type="VENDOR",
            entity_id=vendor.id,
            details={"stage": vendor.current_stage, "is_archived": True}
        )
        db.commit()
