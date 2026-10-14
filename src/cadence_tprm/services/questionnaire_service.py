"""Questionnaire service: dynamic template rendering, versioning, CSV export, show-logic evaluation, and responses.

Source Authority: Cadence_TPRM_Training.docx Section 6.3, Appendix B, Appendix C (CL.1-14), Appendix E (QR.1-90).
"""

import csv
import io
from datetime import datetime, timezone
from typing import Dict, List, Set
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.cadence_tprm.models.questionnaire import (
    QuestionnaireTemplate,
    QuestionnaireSection,
    Question,
    ConditionalRule,
    RiskRule,
)
from src.cadence_tprm.models.assessment import Assessment, QuestionResponse
from src.cadence_tprm.services.audit_service import AuditService

class QuestionnaireService:

    @staticmethod
    def get_template_details(db: Session, template_code: str, current_responses: Dict[str, str] = None) -> dict:
        """Retrieves full questionnaire template structure, CL.1-14 rules, QR.1-90 rules, and computes visible questions."""
        template = db.query(QuestionnaireTemplate).filter_by(code=template_code).first()
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Template {template_code} not found.")

        rules = db.query(ConditionalRule).filter_by(template_code=template_code).all()
        risk_rules = db.query(RiskRule).filter_by(template_code=template_code).all()

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
                    "favorable_answer": q.favorable_answer,
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
            "questionnaire_no": template.questionnaire_no,
            "code": template.code,
            "name": template.name,
            "description": template.description,
            "template_language": template.template_language,
            "template_icon": template.template_icon,
            "source_file_name": template.source_file_name,
            "approver_group": template.approver_group,
            "version": template.version,
            "status": template.status,
            "is_published": template.is_published,
            "sections": sections_output,
            "conditional_rules": [
                {
                    "rule_code": r.rule_code,
                    "section_name": r.section_name,
                    "condition_logic": r.condition_logic,
                    "trigger_question_code": r.trigger_question_code,
                    "trigger_operator": r.trigger_operator,
                    "trigger_response": r.trigger_response,
                    "primary_shown_question": r.primary_shown_question,
                    "copy_logic_to_questions": r.copy_logic_to_questions,
                    "shown_question_codes": r.shown_question_codes,
                    "description": r.description
                }
                for r in rules
            ],
            "risk_rules": [
                {
                    "rule_code": rr.rule_code,
                    "rule_name": rr.rule_name,
                    "condition_logic": rr.condition_logic,
                    "trigger_type": rr.trigger_type,
                    "trigger_question_code": rr.trigger_question_code,
                    "trigger_operator": rr.trigger_operator,
                    "trigger_response": rr.trigger_response,
                    "action_type": rr.action_type,
                    "risk_name": rr.risk_name,
                    "inherent_risk": rr.inherent_risk,
                    "control_id": rr.control_id,
                    "control_name": rr.control_name,
                    "task_name": rr.task_name,
                    "assignee": rr.assignee,
                    "collaborator_group": rr.collaborator_group,
                    "responsible_group": rr.responsible_group,
                    "result_status": rr.result_status,
                    "result_comments": rr.result_comments,
                    "source_notes": rr.source_notes,
                }
                for rr in risk_rules
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
    def create_new_version(db: Session, template_code: str, actor_email: str, method: str = "B", new_name: str = None) -> dict:
        """Implements Section 6.3.3 Questionnaire Versioning:

        - Method A: Duplicate/Copy template into a new draft template code (requires manual workflow update).
        - Method B (Preferred): Create new version of existing published questionnaire, retaining template identity.
        Historical assessments remain bound to their existing responses without rewriting history.
        """
        template = db.query(QuestionnaireTemplate).filter_by(code=template_code).first()
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Template {template_code} not found.")

        if method.upper() == "A":
            new_ver = template.version + 1
            dup_code = f"{template.code.split('_v')[0]}_copy_v{new_ver}_{int(datetime.now(timezone.utc).timestamp()) % 10000}"
            dup = QuestionnaireTemplate(
                questionnaire_no=template.questionnaire_no,
                code=dup_code,
                name=new_name or f"{template.name} (Copy Draft v{new_ver})",
                description=template.description,
                template_language=template.template_language,
                template_icon=template.template_icon,
                source_file_name=template.source_file_name,
                approver_group=template.approver_group,
                version=new_ver,
                status="Draft",
                is_published=False,
                parent_template_id=template.id,
            )
            db.add(dup)
            db.flush()
            for sec in template.sections:
                new_sec = QuestionnaireSection(
                    template_id=dup.id,
                    section_number=sec.section_number,
                    title=sec.title,
                    responsible_group=sec.responsible_group,
                    order_index=sec.order_index,
                )
                db.add(new_sec)
                db.flush()
                for q in sec.questions:
                    db.add(Question(
                        section_id=new_sec.id,
                        question_code=q.question_code,
                        prompt=q.prompt,
                        question_type=q.question_type,
                        options=q.options,
                        favorable_answer=q.favorable_answer,
                        is_required=q.is_required,
                        is_conditional=q.is_conditional,
                        order_index=q.order_index,
                    ))
            AuditService.log_event(
                db,
                actor_email=actor_email,
                action="QUESTIONNAIRE_DUPLICATED_METHOD_A",
                entity_type="QUESTIONNAIRE",
                entity_id=dup.id,
                details={"source_code": template_code, "new_code": dup.code, "version": dup.version}
            )
            db.commit()
            return {"code": dup.code, "name": dup.name, "version": dup.version, "status": dup.status, "method": "A"}

        # Method B: In-place version increment retaining template identity
        template.version = (template.version or 1) + 1
        template.status = "Published"
        template.is_published = True
        template.updated_at = datetime.now(timezone.utc)
        AuditService.log_event(
            db,
            actor_email=actor_email,
            action="QUESTIONNAIRE_VERSION_PUBLISHED_METHOD_B",
            entity_type="QUESTIONNAIRE",
            entity_id=template.id,
            details={"code": template.code, "name": template.name, "new_version": template.version}
        )
        db.commit()
        return {"code": template.code, "name": template.name, "version": template.version, "status": template.status, "method": "B"}

    @staticmethod
    def export_template_csv(db: Session, template_code: str) -> str:
        """Exports structured CSV representation of questionnaire questions per Section 6.3.1."""
        template = db.query(QuestionnaireTemplate).filter_by(code=template_code).first()
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found.")

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["Template Code", "Version", "Section Number", "Section Title", "Responsible Group", "Question Code", "Prompt", "Question Type", "Options", "Is Required", "Is Conditional"])
        for sec in template.sections:
            for q in sec.questions:
                writer.writerow([
                    template.code,
                    template.version,
                    sec.section_number,
                    sec.title,
                    sec.responsible_group,
                    q.question_code,
                    q.prompt,
                    q.question_type,
                    "|".join(q.options) if q.options else "",
                    q.is_required,
                    q.is_conditional,
                ])
        return buf.getvalue()

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
