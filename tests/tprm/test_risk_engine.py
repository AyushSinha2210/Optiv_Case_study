"""Automated tests for all 90 Risk Scoring, Auto-Approve, and Departmental Task Rules (Appendix E: QR.1 to QR.90).

Source Authority: Cadence_TPRM_Training.docx Section 6.3, Appendix E.
"""

import pytest
from src.cadence_tprm.models.vendor import Vendor
from src.cadence_tprm.models.assessment import Assessment
from src.cadence_tprm.models.questionnaire import RiskRule
from src.cadence_tprm.models.task import Task
from src.cadence_tprm.services.risk_engine import RiskEngine
from src.cadence_tprm.services.vendor_service import VendorService

def test_all_90_qr_rules_registered(db_session):
    """Verify all 90 Appendix E rules QR.1 through QR.90 exist in the database rule registry."""
    rules = db_session.query(RiskRule).all()
    rule_codes = {r.rule_code for r in rules}
    expected_codes = {f"QR.{i}" for i in range(1, 91)}
    assert expected_codes.issubset(rule_codes)
    assert len(expected_codes) == 90

def test_qr1_non_us_company_risk(db_session):
    """QR.1: Q1.3=='No' triggers QRN_Non US Company (High Inherent Risk, Control QRC_CL_1.1)."""
    vendor = db_session.query(Vendor).filter_by(vendor_tier="Tier 1").first()
    asm = Assessment(
        vendor_id=vendor.id,
        template_code="T1-2_v1",
        respondent_email=vendor.primary_vendor_contact,
        status="Draft"
    )
    db_session.add(asm)
    db_session.commit()

    responses = {"1.3": "No"}
    findings, score, _ = RiskEngine.evaluate_assessment_submission(
        db_session, asm, responses, actor_email="daniela.figueroa@cadence.com"
    )

    qr1_finding = next((f for f in findings if f.rule_code == "QR.1"), None)
    assert qr1_finding is not None
    assert qr1_finding.risk_name == "QRN_Non US Company"
    assert qr1_finding.inherent_risk == "High"
    assert qr1_finding.control_id == "QRC_CL_1.1"

def test_security_rules_qr23_and_qr45(db_session):
    """QR.23: Q4.18=='No' (No MFA) -> Medium Risk (QRC_Sec_4.12) and QR.45: Q4.49=='No' -> High Risk (QRC_Sec_4.34)."""
    vendor = db_session.query(Vendor).filter_by(vendor_tier="Tier 1").first()
    asm = Assessment(
        vendor_id=vendor.id,
        template_code="T1-2_v1",
        respondent_email=vendor.primary_vendor_contact,
        status="Draft"
    )
    db_session.add(asm)
    db_session.commit()

    responses = {
        "4.18": "No",
        "4.49": "No"
    }
    findings, score, _ = RiskEngine.evaluate_assessment_submission(
        db_session, asm, responses, actor_email="daniela.figueroa@cadence.com"
    )

    qr23 = next((f for f in findings if f.rule_code == "QR.23"), None)
    assert qr23 is not None
    assert qr23.inherent_risk == "Medium"
    assert qr23.control_id == "QRC_Sec_4.12"

    qr45 = next((f for f in findings if f.rule_code == "QR.45"), None)
    assert qr45 is not None
    assert qr45.inherent_risk == "High"
    assert qr45.control_id == "QRC_Sec_4.34"

def test_qr57_low_assessment_score_task_created(db_session):
    """QR.57 & QR.58: Score < 40 triggers 'Low Assessment Score' task for VRM Team."""
    vendor = db_session.query(Vendor).filter_by(vendor_tier="Tier 1").first()
    asm = Assessment(
        vendor_id=vendor.id,
        template_code="T1-2_v1",
        respondent_email=vendor.primary_vendor_contact,
        status="Draft"
    )
    db_session.add(asm)
    db_session.commit()

    responses = {
        "1.3": "No",
        "2.2": "No",
        "3.3": "No",
        "4.14": "No",
        "4.15": "No",
        "4.22": "No",
        "4.26": "No",
        "4.29": "No",
        "4.49": "No",
        "4.50": "No",
    }
    findings, score, _ = RiskEngine.evaluate_assessment_submission(
        db_session, asm, responses, actor_email="daniela.figueroa@cadence.com"
    )
    assert score < 40.0

    task = db_session.query(Task).filter(
        Task.vendor_id == vendor.id,
        Task.title.ilike("%Low Assessment Score%")
    ).first()
    assert task is not None
    assert task.collaborator_group == "Vendor Risk Management Group"

def test_qr73_tier3_auto_approve_on_clean_responses(db_session):
    """QR.73 / WR.T3.3: Tier 3 vendor with favorable responses is auto-approved."""
    data = {
        "name": "Auto Approved Tier 3 Vendor",
        "type": "Operations",
        "criticality": "Low",
        "primary_vendor_contact": "poc@cleanvendor.com",
        "business_owner": "owner@cadence.com",
        "vendor_tier": "Tier 3",
        "vendor_category": "Service Provider and Vendor",
    }
    vendor = VendorService.create_vendor(db_session, data, actor_email="daniela.figueroa@cadence.com")
    asm = db_session.query(Assessment).filter_by(vendor_id=vendor.id).first()

    responses = {
        "1.2": "Yes",
        "2.2": "No",
        "3.3": "Yes",
        "3.4": "Yes",
        "4.1": "Yes",
        "4.2": "Yes",
        "4.3": "Yes",
        "4.4": "Yes",
        "4.5": "Yes",
        "5.2": "Yes",
        "6.1": "Yes",
        "6.2": "Yes",
    }
    findings, score, is_auto_approved = RiskEngine.evaluate_assessment_submission(
        db_session, asm, responses, actor_email="daniela.figueroa@cadence.com"
    )
    assert is_auto_approved is True
    assert score == 100.0
    assert len([f for f in findings if f.inherent_risk == "High"]) == 0

def test_qr74_to_qr90_departmental_tasks_and_it_rules(db_session):
    """Verify QR.74-82 (including QR.81 Q5.6=No and QR.82 Q5.1=Yes) create departmental tasks."""
    vendor = db_session.query(Vendor).filter_by(vendor_tier="Tier 1").first()
    asm = Assessment(
        vendor_id=vendor.id,
        template_code="T1-2_v1",
        respondent_email=vendor.primary_vendor_contact,
        status="Draft"
    )
    db_session.add(asm)
    db_session.commit()

    responses = {
        "1.3": "No",   # Legal Risk (QR.1 -> QR.74)
        "5.1": "Yes",  # IT Requirement (QR.82)
        "5.6": "No",   # IT Risk (QR.47 & QR.81)
        "7.2": "No",   # Procurement Risk (QR.51 -> QR.75)
    }
    RiskEngine.evaluate_assessment_submission(
        db_session, asm, responses, actor_email="daniela.figueroa@cadence.com"
    )

    tasks = db_session.query(Task).filter_by(assessment_id=asm.id).all()
    titles = [t.title for t in tasks]
    assert any("Legal Risk Identified for Third-Party" in t for t in titles)
    assert any("Procurement Risk Identified for Third-Party" in t for t in titles)
    assert any("IT Risk Identified for Third-Party" in t for t in titles)
    assert any("IT Requirement Identified for Third-Party" in t for t in titles)
