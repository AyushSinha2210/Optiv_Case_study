"""Questionnaire template, versioning, question builder, and CSV export endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.cadence_tprm.database import get_db
from src.cadence_tprm.models.questionnaire import QuestionnaireTemplate, QuestionnaireSection, Question, ConditionalRule, RiskRule
from src.cadence_tprm.services.questionnaire_service import QuestionnaireService
from src.cadence_tprm.services.audit_service import AuditService
from src.cadence_tprm.services.auth_service import get_current_user, require_tprm_admin

router = APIRouter(prefix="/questionnaires", tags=["Questionnaires"])

class CreateTemplateRequest(BaseModel):
    name: str
    code: str
    description: str = ""
    template_language: str = "English"
    template_icon: str = "archive"

class VersionTemplateRequest(BaseModel):
    method: str = "B"  # "A" (duplicate draft) or "B" (in-place version increment)
    new_name: Optional[str] = None

class AddQuestionRequest(BaseModel):
    section_number: int = 1
    question_code: str
    prompt: str
    question_type: str = "YesNo"
    options: Optional[List[str]] = ["Yes", "No"]
    favorable_answer: Optional[str] = "Yes"
    is_required: bool = True
    is_conditional: bool = False

@router.get("/templates")
def list_templates(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    templates = db.query(QuestionnaireTemplate).all()
    items = []
    for t in templates:
        cond_count = db.query(ConditionalRule).filter_by(template_code=t.code).count()
        risk_count = db.query(RiskRule).filter_by(template_code=t.code).count()
        q_count = sum(len(s.questions) for s in t.sections)
        items.append({
            "id": t.id,
            "questionnaire_no": t.questionnaire_no,
            "code": t.code,
            "name": t.name,
            "description": t.description,
            "template_language": t.template_language,
            "template_icon": t.template_icon,
            "source_file_name": t.source_file_name,
            "approver_group": t.approver_group,
            "version": t.version,
            "status": t.status,
            "is_published": t.is_published,
            "sections_count": len(t.sections),
            "questions_count": q_count,
            "conditional_rules_count": cond_count,
            "risk_rules_count": risk_count,
        })
    return {"templates": items, "items": items}

@router.post("/templates", status_code=status.HTTP_201_CREATED)
def create_template(
    req: CreateTemplateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_tprm_admin)
):
    if db.query(QuestionnaireTemplate).filter_by(code=req.code.strip()).first():
        raise HTTPException(status_code=400, detail=f"Template code '{req.code}' already exists.")
    t = QuestionnaireTemplate(
        questionnaire_no="Q.Custom",
        code=req.code.strip(),
        name=req.name.strip(),
        description=req.description,
        template_language=req.template_language,
        template_icon=req.template_icon,
        version=1,
        status="Draft",
        is_published=False,
    )
    db.add(t)
    db.flush()
    db.add(QuestionnaireSection(
        template_id=t.id,
        section_number=1,
        title="1. Contracting and Legal",
        responsible_group="Legal Group",
        order_index=1,
    ))
    AuditService.log_event(
        db,
        actor_email=current_user["email"],
        action="QUESTIONNAIRE_TEMPLATE_CREATED",
        entity_type="QUESTIONNAIRE",
        entity_id=t.id,
        details={"code": t.code, "name": t.name}
    )
    db.commit()
    return {"status": "created", "id": t.id, "code": t.code}

@router.get("/templates/{template_code}")
def get_template(
    template_code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return QuestionnaireService.get_template_details(db, template_code)

@router.post("/templates/{template_code}/version")
def create_template_version(
    template_code: str,
    req: VersionTemplateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_tprm_admin)
):
    return QuestionnaireService.create_new_version(
        db,
        template_code=template_code,
        actor_email=current_user["email"],
        method=req.method,
        new_name=req.new_name,
    )

@router.post("/templates/{template_code}/questions", status_code=status.HTTP_201_CREATED)
def add_question_to_template(
    template_code: str,
    req: AddQuestionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_tprm_admin)
):
    template = db.query(QuestionnaireTemplate).filter_by(code=template_code).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found.")

    sec = next((s for s in template.sections if s.section_number == req.section_number), None)
    if not sec:
        sec = QuestionnaireSection(
            template_id=template.id,
            section_number=req.section_number,
            title=f"Section {req.section_number}",
            responsible_group="Vendor Risk Management Group",
            order_index=req.section_number,
        )
        db.add(sec)
        db.flush()

    q = Question(
        section_id=sec.id,
        question_code=req.question_code.strip(),
        prompt=req.prompt.strip(),
        question_type=req.question_type,
        options=req.options,
        favorable_answer=req.favorable_answer,
        is_required=req.is_required,
        is_conditional=req.is_conditional,
        order_index=len(sec.questions) + 1,
    )
    db.add(q)
    AuditService.log_event(
        db,
        actor_email=current_user["email"],
        action="QUESTION_ADDED_TO_TEMPLATE",
        entity_type="QUESTIONNAIRE",
        entity_id=template.id,
        details={"template_code": template_code, "question_code": q.question_code}
    )
    db.commit()
    return {"status": "question_added", "question_code": q.question_code}

@router.get("/templates/{template_code}/export-csv")
def export_template_csv(
    template_code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    csv_data = QuestionnaireService.export_template_csv(db, template_code)
    AuditService.log_event(
        db,
        actor_email=current_user["email"],
        action="QUESTIONNAIRE_CSV_EXPORTED",
        entity_type="QUESTIONNAIRE",
        entity_id=template_code,
        details={"template_code": template_code}
    )
    return PlainTextResponse(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{template_code}_questions.csv"'},
    )
