"""Questionnaire service: dynamic template rendering, show-logic evaluation, and responses.

Source Authority: Cadence_TPRM_Training.docx Section 6.3, Appendix C, Table 12 (CL.1-14).
"""

from typing import Dict, List, Set, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.cadence_tprm.models.questionnaire import (
    QuestionnaireTemplate,
    QuestionnaireSection,
    Question,
    ConditionalRule,
)
from src.cadence_tprm.models.assessment import Assessment, QuestionResponse

class QuestionnaireService:

    @staticmethod
    def get_template_details(db: Session, template_code: str, current_responses: Dict[str, str] = None) -> dict:
        """Retrieves full questionnaire template structure and computes visible questions."""
        template = db.query(QuestionnaireTemplate).filter_by(code=template_code).first()
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Template {template_code} not found.")

        # Load conditional rules for template
        rules = db.query(ConditionalRule).filter_by(template_code=template_code).all()

        # Compute which questions should be visible
        visible_question_codes = QuestionnaireService.compute_visible_questions(rules, current_responses or {})

        sections_output = []
        for sec in template.sections:
            sec_questions = []
            for q in sec.questions:
                is_visible = (not q.is_conditional) or (q.question_code in visible_question_codes)
                sec_questions.append({
                    "id": q.id,
                    "question_code": q.question_code,
                    "prompt": q.prompt,
                    "question_type": q.question_type,
                    "options": q.options,
                    "is_required": q.is_required,
                    "is_conditional": q.is_conditional,
                    "is_visible": is_visible,
                    "order_index": q.order_index,
                })

            sections_output.append({
                "id": sec.id,
                "section_number": sec.section_number,
                "title": sec.title,
                "responsible_group": sec.responsible_group,
                "questions": sec_questions
            })

        return {
            "id": template.id,
            "code": template.code,
            "name": template.name,
            "description": template.description,
            "version": template.version,
            "sections": sections_output,
            "conditional_rules": [
                {
                    "rule_code": r.rule_code,
                    "trigger_question_code": r.trigger_question_code,
                    "trigger_response": r.trigger_response,
                    "shown_question_codes": r.shown_question_codes,
                    "description": r.description
                }
                for r in rules
            ]
        }

    @staticmethod
    def compute_visible_questions(rules: List[ConditionalRule], responses: Dict[str, str]) -> Set[str]:
        """Evaluates CL.1 to CL.14 show-logic rules."""
        visible_codes = set()
        for rule in rules:
            ans = responses.get(rule.trigger_question_code)
            if ans and str(ans).strip().lower() == str(rule.trigger_response).strip().lower():
                if isinstance(rule.shown_question_codes, list):
                    for code in rule.shown_question_codes:
                        visible_codes.add(code)
        return visible_codes

    @staticmethod
    def save_responses(db: Session, assessment_id: str, responses: Dict[str, str]):
        """Persists or updates question responses for an assessment."""
        assessment = db.query(Assessment).filter_by(id=assessment_id).first()
        if not assessment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")

        if assessment.status in ["Approved", "Rejected"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot edit a finalized assessment.")

        for q_code, val in responses.items():
            existing = (
                db.query(QuestionResponse)
                .filter_by(assessment_id=assessment_id, question_code=q_code)
                .first()
            )
            if existing:
                existing.response_value = str(val)
            else:
                db.add(QuestionResponse(
                    assessment_id=assessment_id,
                    question_code=q_code,
                    response_value=str(val)
                ))
        db.commit()

    @staticmethod
    def validate_responses_for_submission(db: Session, assessment: Assessment, responses: Dict[str, str]):
        """Validates that all required visible questions have responses."""
        template = db.query(QuestionnaireTemplate).filter_by(code=assessment.template_code).first()
        rules = db.query(ConditionalRule).filter_by(template_code=assessment.template_code).all()
        visible_codes = QuestionnaireService.compute_visible_questions(rules, responses)

        missing = []
        for sec in template.sections:
            for q in sec.questions:
                is_visible = (not q.is_conditional) or (q.question_code in visible_codes)
                if is_visible and q.is_required:
                    val = responses.get(q.question_code)
                    if not val or not str(val).strip():
                        missing.append(q.question_code)

        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot submit assessment: required questions unanswered: {', '.join(missing[:5])} (Total missing: {len(missing)})"
            )
