"""Automated tests for Workflow FSM Engine and Routing Rules WR.ON.1 to WR.ON.6.

Source Authority: Cadence_TPRM_Training.docx Section 4.2, 5.1, Appendix A, Tables 6, 7, 8, 10.
"""

import pytest
from src.cadence_tprm.models.vendor import Vendor
from src.cadence_tprm.models.assessment import Assessment
from src.cadence_tprm.models.task import Task
from src.cadence_tprm.services.workflow_engine import WorkflowEngine
from src.cadence_tprm.services.vendor_service import VendorService

def test_workflow_rule_on_1_revenue_partner(db_session):
    """WR.ON.1: Revenue Partner Tier 1/2 routes to CD_Revenue Partners Workflow in stage Launching RevPart."""
    data = {
        "name": "Affiliate Revenue Corp",
        "type": "Strategic",
        "criticality": "High",
        "primary_vendor_contact": "poc@affiliaterev.com",
        "business_owner": "owner@cadence.com",
        "vendor_tier": "Tier 1",
        "vendor_category": "Revenue Partner",
    }
    v = VendorService.create_vendor(db_session, data, actor_email="daniela.figueroa@cadence.com")
    assert v.current_workflow_name == "CD_Revenue Partners Workflow"
    assert v.current_stage == "Launching RevPart"
    assert v.lifecycle_status == "In Progress"

    # Verify assessment dispatched with T1-2 template
    asm = db_session.query(Assessment).filter_by(vendor_id=v.id).first()
    assert asm is not None
    assert asm.template_code == "T1-2_v1"

def test_workflow_rule_on_2_marketing_partner(db_session):
    """WR.ON.2: Marketing Partner Tier 1/2 routes to CD_Marketing Partners Workflow in stage Launching MarPart."""
    data = {
        "name": "Omni Campaign Agency",
        "type": "Operations",
        "criticality": "Medium",
        "primary_vendor_contact": "poc@omnicampaign.com",
        "business_owner": "owner@cadence.com",
        "vendor_tier": "Tier 2",
        "vendor_category": "Marketing Partner",
    }
    v = VendorService.create_vendor(db_session, data, actor_email="daniela.figueroa@cadence.com")
    assert v.current_workflow_name == "CD_Marketing Partners Workflow"
    assert v.current_stage == "Launching MarPart"

def test_workflow_rule_on_3_international_vendor(db_session):
    """WR.ON.3: International Vendor Tier 1/2 routes to CD_International Vendors Workflow in stage Launching IntVen."""
    data = {
        "name": "Nordic Analytics AB",
        "type": "Consulting",
        "criticality": "High",
        "primary_vendor_contact": "poc@nordicanalytics.se",
        "business_owner": "owner@cadence.com",
        "vendor_tier": "Tier 1",
        "vendor_category": "International Vendor",
    }
    v = VendorService.create_vendor(db_session, data, actor_email="daniela.figueroa@cadence.com")
    assert v.current_workflow_name == "CD_International Vendors Workflow"
    assert v.current_stage == "Launching IntVen"

def test_workflow_rule_on_4_service_providers(db_session):
    """WR.ON.4: Service Provider and Vendor Tier 1/2 routes to CD_Service Providers Workflow in stage Launching ServPro."""
    data = {
        "name": "Cloud Operations BPO",
        "type": "Technology",
        "criticality": "Medium",
        "primary_vendor_contact": "poc@cloudopsbpo.com",
        "business_owner": "owner@cadence.com",
        "vendor_tier": "Tier 2",
        "vendor_category": "Service Provider and Vendor",
    }
    v = VendorService.create_vendor(db_session, data, actor_email="daniela.figueroa@cadence.com")
    assert v.current_workflow_name == "CD_Service Providers Workflow"
    assert v.current_stage == "Launching ServPro"

def test_workflow_rule_on_5_staffing_vendor(db_session):
    """WR.ON.5: Staffing Vendor Tier 1/2 routes to CD_Staffing Vendors Workflow in stage Launching StafVen."""
    data = {
        "name": "Tech Talent Resources",
        "type": "Operations",
        "criticality": "Medium",
        "primary_vendor_contact": "poc@techtalent.com",
        "business_owner": "owner@cadence.com",
        "vendor_tier": "Tier 2",
        "vendor_category": "Staffing Vendor",
    }
    v = VendorService.create_vendor(db_session, data, actor_email="daniela.figueroa@cadence.com")
    assert v.current_workflow_name == "CD_Staffing Vendors Workflow"
    assert v.current_stage == "Launching StafVen"

def test_workflow_rule_on_6_tier3_vendor(db_session):
    """WR.ON.6: Tier 3 Vendor routes to CD_Tier3 Workflow in stage Launching Tier3 (regardless of category)."""
    data = {
        "name": "Local Office Supplies Co",
        "type": "Operations",
        "criticality": "Low",
        "primary_vendor_contact": "poc@localoffice.com",
        "business_owner": "owner@cadence.com",
        "vendor_tier": "Tier 3",  # Triggers WR.ON.6
        "vendor_category": "Service Provider and Vendor",
    }
    v = VendorService.create_vendor(db_session, data, actor_email="daniela.figueroa@cadence.com")
    assert v.current_workflow_name == "CD_Tier3 Workflow"
    assert v.current_stage == "Launching Tier3"

    # Verify assessment uses simplified T3_v1 template
    asm = db_session.query(Assessment).filter_by(vendor_id=v.id).first()
    assert asm is not None
    assert asm.template_code == "T3_v1"

def test_workflow_approval_advances_to_live(db_session):
    """WR.*.3: Approval moves vendor to Live stage and calculates reassessment due date."""
    data = {
        "name": "FastTrack Approvals Inc",
        "type": "Technology",
        "criticality": "Medium",
        "primary_vendor_contact": "poc@fasttrack.com",
        "business_owner": "owner@cadence.com",
        "vendor_tier": "Tier 1",
        "vendor_category": "Service Provider and Vendor",
    }
    v = VendorService.create_vendor(db_session, data, actor_email="daniela.figueroa@cadence.com")
    asm = db_session.query(Assessment).filter_by(vendor_id=v.id).first()

    WorkflowEngine.approve_vendor(
        db_session, v, asm,
        actor_email="daniela.figueroa@cadence.com",
        reason="Due diligence review complete and satisfactory."
    )

    assert v.lifecycle_status == "Live"
    assert v.current_stage == "Live"
    assert asm.status == "Approved"
    assert v.last_assessment_completion_date is not None
    assert v.next_reassessment_due_date is not None

def test_workflow_rejection_moves_to_review_reject_with_14_day_task(db_session):
    """WR.*.4 and WR.*.5: Rejection moves vendor to Review Reject and creates 14-day task for business owner."""
    data = {
        "name": "Rejected Vendor Corp",
        "type": "Technology",
        "criticality": "High",
        "primary_vendor_contact": "poc@rejectedcorp.com",
        "business_owner": "owner@cadence.com",
        "vendor_tier": "Tier 1",
        "vendor_category": "Service Provider and Vendor",
    }
    v = VendorService.create_vendor(db_session, data, actor_email="daniela.figueroa@cadence.com")
    asm = db_session.query(Assessment).filter_by(vendor_id=v.id).first()

    WorkflowEngine.reject_vendor(
        db_session, v, asm,
        actor_email="daniela.figueroa@cadence.com",
        reason="Vendor failed critical security requirements."
    )

    assert v.lifecycle_status == "Review Reject"
    assert "Review Reject" in v.current_stage
    assert asm.status == "Rejected"

    # Verify WR.*.5 task created with 14-day deadline
    task = db_session.query(Task).filter_by(vendor_id=v.id, task_type="Review Reject Followup").first()
    assert task is not None
    assert task.assignee_email == "owner@cadence.com"
    assert task.collaborator_group == "Vendor Risk Management Group"
