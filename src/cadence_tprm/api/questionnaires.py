"""Questionnaire template and structure endpoints."""

from typing import Dict, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.cadence_tprm.database import get_db
from src.cadence_tprm.models.questionnaire import QuestionnaireTemplate
from src.cadence_tprm.services.questionnaire_service import QuestionnaireService
from src.cadence_tprm.services.auth_service import get_current_user

router = APIRouter(prefix="/questionnaires", tags=["Questionnaires"])

@router.get("/templates")
def list_templates(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    templates = db.query(QuestionnaireTemplate).all()
    return {
        "templates": [
            {
                "id": t.id,
                "code": t.code,
                "name": t.name,
                "description": t.description,
                "version": t.version,
                "is_published": t.is_published,
                "sections_count": len(t.sections),
            }
            for t in templates
        ]
    }

@router.get("/templates/{template_code}")
def get_template(
    template_code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return QuestionnaireService.get_template_details(db, template_code)
