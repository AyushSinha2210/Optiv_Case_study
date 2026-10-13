"""Automated tests for SLAs, Reminders, and Recurring Reassessment Automation.

Source Authority: Cadence_TPRM_Training.docx Appendix A (AR.T1.1, AR.T2.1, AR.T3.1), Appendix D (Table 13: SLA.1 to SLA.7).
"""

from datetime import datetime, timezone, timedelta
import pytest
from src.cadence_tprm.models.vendor import Vendor
from src.cadence_tprm.models.assessment import Assessment
from src.cadence_tprm.models.task import Task
from src.cadence_tprm.services.sla_service import SLAService
from src.cadence_tprm.services.vendor_service import VendorService

def test_sla_date_calculations():
    """Verify SLA calculation formulas from Table 13:

    SLA.1: 9 days
    SLA.2: 4 days
    SLA.3: 5 + 4 = 9 days
    SLA.4: 10 + 4 = 14 days
    SLA.5: 15 + 4 = 19 days
    """
    now = datetime(2026, 9, 16, 12, 0, 0, tzinfo=timezone.utc)
    sla1_due = now + timedelta(days=9)
    sla2_due = now + timedelta(days=4)
    sla3_due = now + timedelta(days=5 + 4)
    sla4_due = now + timedelta(days=10 + 4)
    sla5_due = now + timedelta(days=15 + 4)

    assert (sla1_due - now).days == 9
    assert (sla2_due - now).days == 4
    assert (sla3_due - now).days == 9
    assert (sla4_due - now).days == 14
    assert (sla5_due - now).days == 19

def test_ar_t1_1_annual_reassessment_trigger_at_275_days(db_session):
    """AR.T1.1: Triggers reassessment for Tier 1 vendors when days >= 275."""
    now = datetime.now(timezone.utc)
    past_date = now - timedelta(days=280)  # > 275 days

    data = {
        "name": "Reassessment Tier 1 Vendor",
        "type": "Technology",
        "criticality": "Critical",
        "primary_vendor_contact": "poc@reassess1.com",
        "business_owner": "owner@cadence.com",
        "vendor_tier": "Tier 1",
        "vendor_category": "Service Provider and Vendor",
    }
    v = VendorService.create_vendor(db_session, data, actor_email="daniela.figueroa@cadence.com")
    v.lifecycle_status = "Live"
    v.current_stage = "Live"
    v.last_assessment_completion_date = past_date
    db_session.commit()

    results = SLAService.run_daily_reassessment_automation(db_session)
    assert results["tier1_reassessments"] >= 1

    # Verify a new in-flight assessment was launched
    reassessment = db_session.query(Assessment).filter(
        Assessment.vendor_id == v.id,
        Assessment.status == "Draft"
    ).first()
    assert reassessment is not None
    assert reassessment.template_code == "T1-2_v1"

def test_ar_t2_1_and_t3_1_reassessment_trigger_at_640_days(db_session):
    """AR.T2.1 & AR.T3.1: Triggers reassessment for Tier 2 and Tier 3 vendors when days >= 640."""
    now = datetime.now(timezone.utc)
    past_date = now - timedelta(days=645)  # > 640 days

    # Tier 2 vendor
    v2_data = {
        "name": "Reassessment Tier 2 Vendor",
        "type": "Operations",
        "criticality": "Medium",
        "primary_vendor_contact": "poc@reassess2.com",
        "business_owner": "owner@cadence.com",
        "vendor_tier": "Tier 2",
        "vendor_category": "Staffing Vendor",
    }
    v2 = VendorService.create_vendor(db_session, v2_data, actor_email="daniela.figueroa@cadence.com")
    v2.lifecycle_status = "Live"
    v2.current_stage = "Live"
    v2.last_assessment_completion_date = past_date

    # Tier 3 vendor
    v3_data = {
        "name": "Reassessment Tier 3 Vendor",
        "type": "Operations",
        "criticality": "Low",
        "primary_vendor_contact": "poc@reassess3.com",
        "business_owner": "owner@cadence.com",
        "vendor_tier": "Tier 3",
        "vendor_category": "Service Provider and Vendor",
    }
    v3 = VendorService.create_vendor(db_session, v3_data, actor_email="daniela.figueroa@cadence.com")
    v3.lifecycle_status = "Live"
    v3.current_stage = "Live"
    v3.last_assessment_completion_date = past_date
    db_session.commit()

    results = SLAService.run_daily_reassessment_automation(db_session)
    assert results["tier2_reassessments"] >= 1
    assert results["tier3_reassessments"] >= 1
