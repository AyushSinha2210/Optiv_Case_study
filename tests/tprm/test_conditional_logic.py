"""Automated tests for all 14 Conditional Logic Rules CL.1 to CL.14.

Source Authority: Cadence_TPRM_Training.docx Section 6.3, Appendix C.
"""

import pytest
from src.cadence_tprm.models.questionnaire import ConditionalRule
from src.cadence_tprm.services.questionnaire_service import QuestionnaireService

def test_all_14_conditional_rules_seeded_in_registry(db_session):
    """Verify all 14 rules CL.1 through CL.14 exist in the database registry."""
    rules = db_session.query(ConditionalRule).all()
    codes = {r.rule_code for r in rules}
    expected = {f"CL.{i}" for i in range(1, 15)}
    assert expected.issubset(codes)

def test_cl1_foreign_incorporation_reveals_questions(db_session):
    """CL.1: Q1.5=='Yes' shows Q1.6, Q1.7, Q1.8."""
    rules = db_session.query(ConditionalRule).filter_by(template_code="T1-2_v1").all()

    visible = QuestionnaireService.compute_visible_questions(rules, {"1.5": "No"})
    assert "1.6" not in visible
    assert "1.7" not in visible
    assert "1.8" not in visible

    visible = QuestionnaireService.compute_visible_questions(rules, {"1.5": "Yes"})
    assert "1.6" in visible
    assert "1.7" in visible
    assert "1.8" in visible

def test_cl2_cl3_cl4_conditional_display(db_session):
    """CL.2 (Q2.4=Yes->2.5), CL.3 (Q3.6=No->3.7), CL.4 (Q4.4=Yes->4.5, 4.6)."""
    rules = db_session.query(ConditionalRule).filter_by(template_code="T1-2_v1").all()

    visible = QuestionnaireService.compute_visible_questions(rules, {"2.4": "Yes", "3.6": "No", "4.4": "Yes"})
    assert "2.5" in visible
    assert "3.7" in visible
    assert "4.5" in visible
    assert "4.6" in visible

def test_cl5_ai_questions_revealed_on_yes(db_session):
    """CL.5: Q4.10=='Yes' shows Q4.11, Q4.12, Q4.13."""
    rules = db_session.query(ConditionalRule).filter_by(template_code="T1-2_v1").all()

    visible = QuestionnaireService.compute_visible_questions(rules, {"4.10": "Yes"})
    assert "4.11" in visible
    assert "4.12" in visible
    assert "4.13" in visible

def test_cl6_mfa_justification_revealed_on_no(db_session):
    """CL.6: Q4.18=='No' shows Q4.19."""
    rules = db_session.query(ConditionalRule).filter_by(template_code="T1-2_v1").all()

    visible = QuestionnaireService.compute_visible_questions(rules, {"4.18": "Yes"})
    assert "4.19" not in visible

    visible = QuestionnaireService.compute_visible_questions(rules, {"4.18": "No"})
    assert "4.19" in visible

def test_cl7_cl8_cl9_cl10_cl11_cl12_cl13_conditional_display(db_session):
    """CL.7 (4.20=Yes->4.21), CL.8 (4.24=Yes->4.25), CL.9 (4.26=Yes->4.27), CL.10 (4.30=Yes->4.31), CL.11 (4.34=Yes->4.35), CL.12 (4.36=Yes->4.37), CL.13 (8.1=Yes->8.2)."""
    rules = db_session.query(ConditionalRule).filter_by(template_code="T1-2_v1").all()
    visible = QuestionnaireService.compute_visible_questions(rules, {
        "4.20": "Yes",
        "4.24": "Yes",
        "4.26": "Yes",
        "4.30": "Yes",
        "4.34": "Yes",
        "4.36": "Yes",
        "8.1": "Yes",
    })
    for target in ["4.21", "4.25", "4.27", "4.31", "4.35", "4.37", "8.2"]:
        assert target in visible

def test_cl3_and_cl14_oracle_vendor_form_logic(db_session):
    """CL.3 (T1-2 Q3.6=='No' -> Q3.7) and CL.14 (T3 Q3.4=='No' -> Q3.5)."""
    t1_rules = db_session.query(ConditionalRule).filter_by(template_code="T1-2_v1").all()
    t3_rules = db_session.query(ConditionalRule).filter_by(template_code="T3_v1").all()

    v1 = QuestionnaireService.compute_visible_questions(t1_rules, {"3.6": "No"})
    assert "3.7" in v1

    v3 = QuestionnaireService.compute_visible_questions(t3_rules, {"3.4": "No"})
    assert "3.5" in v3

def test_cl10_security_incident_disclosure(db_session):
    """CL.10: Q4.30=='Yes' shows Q4.31."""
    rules = db_session.query(ConditionalRule).filter_by(template_code="T1-2_v1").all()
    visible = QuestionnaireService.compute_visible_questions(rules, {"4.30": "Yes"})
    assert "4.31" in visible
