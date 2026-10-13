"""Automated tests for Conditional Logic Rules CL.1 to CL.14.

Source Authority: Cadence_TPRM_Training.docx Section 6.3, Appendix C, Table 12.
"""

import pytest
from src.cadence_tprm.models.questionnaire import ConditionalRule
from src.cadence_tprm.services.questionnaire_service import QuestionnaireService

def test_cl1_foreign_incorporation_reveals_questions(db_session):
    """CL.1: Q1.5=='Yes' shows Q1.6, Q1.7, Q1.8."""
    rules = db_session.query(ConditionalRule).filter_by(template_code="T1-2_v1").all()
    
    # When Q1.5 is "No"
    visible = QuestionnaireService.compute_visible_questions(rules, {"1.5": "No"})
    assert "1.6" not in visible
    assert "1.7" not in visible
    assert "1.8" not in visible

    # When Q1.5 is "Yes"
    visible = QuestionnaireService.compute_visible_questions(rules, {"1.5": "Yes"})
    assert "1.6" in visible
    assert "1.7" in visible
    assert "1.8" in visible

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
    
    # When MFA is Yes -> 4.19 not required
    visible = QuestionnaireService.compute_visible_questions(rules, {"4.18": "Yes"})
    assert "4.19" not in visible

    # When MFA is No -> 4.19 required
    visible = QuestionnaireService.compute_visible_questions(rules, {"4.18": "No"})
    assert "4.19" in visible

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
