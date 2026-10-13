"""Authoritative Workflow Finite State Machine (FSM) Engine.

Source Authority: Cadence_TPRM_Training.docx Section 4.2, 5.1, 6.4, Appendix A, Tables 6, 7, 8, 10.
"""

from typing import Tuple, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.cadence_tprm.models.vendor import Vendor
from src.cadence_tprm.models.assessment import Assessment
from src.cadence_tprm.models.workflow import Workflow, WorkflowInstance, WorkflowTransition
from src.cadence_tprm.models.task import Task, Notification
from src.cadence_tprm.services.audit_service import AuditService

class WorkflowEngine:

    @staticmethod
    def route_new_vendor(db: Session, vendor: Vendor, actor_email: str) -> str:
        """Evaluates Onboarding stage rules WR.ON.1 to WR.ON.6.

        Routes vendor from CD_Onboarding Workflow to the target tier/category workflow.
        """
        # Determine target workflow & initial launch stage
        target_workflow = None
        launch_stage = None
        rule_name = None

        tier = vendor.vendor_tier
        category = vendor.vendor_category

        if tier == "Tier 3":
            # WR.ON.6: Tier 3 rule takes precedence across all categories
            target_workflow = "CD_Tier3 Workflow"
            launch_stage = "Launching Tier3"
            rule_name = "WR.ON.6"
        elif category == "Revenue Partner" and tier in ["Tier 1", "Tier 2"]:
            target_workflow = "CD_Revenue Partners Workflow"
            launch_stage = "Launching RevPart"
            rule_name = "WR.ON.1"
        elif category == "Marketing Partner" and tier in ["Tier 1", "Tier 2"]:
            target_workflow = "CD_Marketing Partners Workflow"
            launch_stage = "Launching MarPart"
            rule_name = "WR.ON.2"
        elif category == "International Vendor" and tier in ["Tier 1", "Tier 2"]:
            target_workflow = "CD_International Vendors Workflow"
            launch_stage = "Launching IntVen"
            rule_name = "WR.ON.3"
        elif category == "Service Provider and Vendor" and tier in ["Tier 1", "Tier 2"]:
            target_workflow = "CD_Service Providers Workflow"
            launch_stage = "Launching ServPro"
            rule_name = "WR.ON.4"
        elif category == "Staffing Vendor" and tier in ["Tier 1", "Tier 2"]:
            target_workflow = "CD_Staffing Vendors Workflow"
            launch_stage = "Launching StafVen"
            rule_name = "WR.ON.5"
        else:
            # Fallback default for undefined pairings
            target_workflow = "CD_Service Providers Workflow"
            launch_stage = "Launching ServPro"
            rule_name = "WR.ON.DEFAULT"

        # Update vendor record
        old_stage = vendor.current_stage
        vendor.current_workflow_name = target_workflow
        vendor.current_stage = launch_stage
        vendor.lifecycle_status = "In Progress"

        # Find or create workflow instance
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

        # Log transition
        transition = WorkflowTransition(
            instance_id=wf_instance.id,
            actor_email=actor_email,
            from_stage=old_stage,
            to_stage=launch_stage,
            trigger_name="On_T_Assign Workflow",
            rule_name=rule_name,
            decision_reason=f"Routed based on Category='{category}' and Tier='{tier}'."
        )
        db.add(transition)

        # Launch appropriate assessment per WR.*.2 or WR.T3.2
        template_code = "T3_v1" if tier == "Tier 3" else "T1-2_v1"
        assessment = Assessment(
            vendor_id=vendor.id,
            template_code=template_code,
            respondent_email=vendor.primary_vendor_contact,
            approver_group="Vendor Risk Management Group",
            status="Draft",
            due_date=datetime.now(timezone.utc) + timedelta(days=9),  # SLA.1 (9 days)
        )
        db.add(assessment)
        db.flush()

        # Send launch notification to Primary Vendor Contact
        db.add(Notification(
            recipient_email=vendor.primary_vendor_contact,
            subject=f"Cadence Due Diligence Assessment: {vendor.name}",
            body=f"Please complete the required Due Diligence Assessment ({template_code}) within 9 business days.",
            notification_type="InApp",
            link_url=f"/assessments/{assessment.id}"
        ))

        # Send notification to Business Owner
        db.add(Notification(
            recipient_email=vendor.business_owner,
            subject=f"Vendor Onboarding Initiated: {vendor.name}",
            body=f"Vendor '{vendor.name}' has been classified as {tier} ({category}). Due diligence questionnaire dispatched.",
            notification_type="InApp"
        ))

        # Audit event
        AuditService.log_event(
            db,
            actor_email=actor_email,
            action="WORKFLOW_ROUTED",
            entity_type="VENDOR",
            entity_id=vendor.id,
            details={
                "target_workflow": target_workflow,
                "launch_stage": launch_stage,
                "rule_name": rule_name,
                "assessment_id": assessment.id
            }
        )

        db.commit()
        return target_workflow

    @staticmethod
    def approve_vendor(db: Session, vendor: Vendor, assessment: Assessment, actor_email: str, reason: str):
        """Applies WR.*.3 (Approval transition to Live) and WR.*.6 (Approval notification)."""
        if vendor.lifecycle_status == "Live":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vendor is already in Live status.")

        old_stage = vendor.current_stage
        vendor.current_stage = "Live"
        vendor.lifecycle_status = "Live"
        vendor.last_assessment_completion_date = datetime.now(timezone.utc)
        
        # Calculate next reassessment due date per Table 13 SLA.6/7
        reassessment_days = 365 if vendor.vendor_tier == "Tier 1" else 730
        vendor.next_reassessment_due_date = vendor.last_assessment_completion_date + timedelta(days=reassessment_days)

        assessment.status = "Approved"
        assessment.completed_at = datetime.now(timezone.utc)
        assessment.decision_reason = reason
        assessment.decision_by = actor_email

        # Record transition
        wf_inst = db.query(WorkflowInstance).filter_by(vendor_id=vendor.id).order_by(WorkflowInstance.started_at.desc()).first()
        if wf_inst:
            db.add(WorkflowTransition(
                instance_id=wf_inst.id,
                actor_email=actor_email,
                from_stage=old_stage,
                to_stage="Live",
                trigger_name="Assessment Approved",
                rule_name="WR.*.3",
                decision_reason=reason
            ))

        # Rule WR.*.6: Notify approval
        db.add(Notification(
            recipient_email=vendor.business_owner,
            subject=f"Vendor Approved: {vendor.name}",
            body=f"Third-Party '{vendor.name}' has been successfully approved and moved to Live stage.",
            notification_type="InApp"
        ))
        db.add(Notification(
            recipient_email=vendor.primary_vendor_contact,
            subject=f"Cadence TPRM - Assessment Approved: {vendor.name}",
            body=f"Your due diligence assessment for '{vendor.name}' has been validated and approved.",
            notification_type="InApp"
        ))

        # Close pending assessment tasks
        tasks = db.query(Task).filter_by(vendor_id=vendor.id, status="Pending").all()
        for t in tasks:
            if "Assessment" in t.task_type:
                t.status = "Completed"
                t.completed_at = datetime.now(timezone.utc)

        AuditService.log_event(
            db,
            actor_email=actor_email,
            action="VENDOR_APPROVED",
            entity_type="VENDOR",
            entity_id=vendor.id,
            details={"reason": reason, "previous_stage": old_stage, "new_stage": "Live"}
        )

        db.commit()

    @staticmethod
    def reject_vendor(db: Session, vendor: Vendor, assessment: Assessment, actor_email: str, reason: str):
        """Applies WR.*.4 (Transition to Review Reject) and WR.*.5 (Notification & 14-day task)."""
        old_stage = vendor.current_stage
        reject_stage = f"Review Reject {vendor.current_workflow_name.replace('CD_', '').replace(' Workflow', '')}"
        
        vendor.current_stage = reject_stage
        vendor.lifecycle_status = "Review Reject"

        assessment.status = "Rejected"
        assessment.completed_at = datetime.now(timezone.utc)
        assessment.decision_reason = reason
        assessment.decision_by = actor_email

        # Record transition
        wf_inst = db.query(WorkflowInstance).filter_by(vendor_id=vendor.id).order_by(WorkflowInstance.started_at.desc()).first()
        if wf_inst:
            db.add(WorkflowTransition(
                instance_id=wf_inst.id,
                actor_email=actor_email,
                from_stage=old_stage,
                to_stage=reject_stage,
                trigger_name="Assessment Rejected",
                rule_name="WR.*.4",
                decision_reason=reason
            ))

        # Rule WR.*.5: Notify rejection AND create 14-day task for Business Owner
        db.add(Notification(
            recipient_email=vendor.business_owner,
            subject=f"URGENT: Third-Party Rejected - {vendor.name}",
            body=f"Vendor '{vendor.name}' has been rejected. Reason: {reason}. Review required within 14 days.",
            notification_type="InApp"
        ))

        db.add(Task(
            vendor_id=vendor.id,
            assessment_id=assessment.id,
            task_type="Review Reject Followup",
            title=f"Review Vendor Rejection: {vendor.name}",
            description=f"Follow up on vendor rejection. Decision reason: {reason}. Coordinate offboarding or remediation.",
            assignee_email=vendor.business_owner,
            collaborator_group="Vendor Risk Management Group",
            due_date=datetime.now(timezone.utc) + timedelta(days=14),
            status="Pending"
        ))

        AuditService.log_event(
            db,
            actor_email=actor_email,
            action="VENDOR_REJECTED",
            entity_type="VENDOR",
            entity_id=vendor.id,
            details={"reason": reason, "previous_stage": old_stage, "new_stage": reject_stage}
        )

        db.commit()

    @staticmethod
    def initiate_offboarding(db: Session, vendor: Vendor, actor_email: str, reason: str):
        """Transitions vendor to Offboarding status."""
        old_stage = vendor.current_stage
        vendor.current_stage = "Offboarding Review"
        vendor.lifecycle_status = "Offboarding"

        # Record transition
        wf_inst = db.query(WorkflowInstance).filter_by(vendor_id=vendor.id).order_by(WorkflowInstance.started_at.desc()).first()
        if wf_inst:
            db.add(WorkflowTransition(
                instance_id=wf_inst.id,
                actor_email=actor_email,
                from_stage=old_stage,
                to_stage="Offboarding Review",
                trigger_name="Offboarding Initiated",
                rule_name="OFFBOARDING_TRIGGER",
                decision_reason=reason
            ))

        # Notify stakeholders
        db.add(Notification(
            recipient_email=vendor.business_owner,
            subject=f"Offboarding Initiated: {vendor.name}",
            body=f"Offboarding process initiated for vendor '{vendor.name}'. Deprovisioning activities started.",
            notification_type="InApp"
        ))

        # Create offboarding checklist task
        db.add(Task(
            vendor_id=vendor.id,
            task_type="Offboarding Verification",
            title=f"Offboarding & Asset Revocation: {vendor.name}",
            description=f"Revoke all system access, reclaim credentials, terminate contracts. Reason: {reason}.",
            assignee_email=actor_email,
            collaborator_group="Security Group",
            due_date=datetime.now(timezone.utc) + timedelta(days=7),
            status="Pending"
        ))

        AuditService.log_event(
            db,
            actor_email=actor_email,
            action="OFFBOARDING_INITIATED",
            entity_type="VENDOR",
            entity_id=vendor.id,
            details={"reason": reason}
        )

        db.commit()

    @staticmethod
    def close_vendor(db: Session, vendor: Vendor, actor_email: str):
        """Transitions vendor to final Closed stage."""
        old_stage = vendor.current_stage
        vendor.current_stage = "Closed"
        vendor.lifecycle_status = "Closed"

        AuditService.log_event(
            db,
            actor_email=actor_email,
            action="VENDOR_CLOSED",
            entity_type="VENDOR",
            entity_id=vendor.id,
            details={"previous_stage": old_stage, "new_stage": "Closed"}
        )
        db.commit()
