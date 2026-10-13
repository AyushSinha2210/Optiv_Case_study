"""Assessment submission, response drafting, risk evaluation, and approval/rejection endpoints."""

from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.cadence_tprm.database import get_db
from src.cadence_tprm.models.assessment import Assessment, AssessmentReview
from src.cadence_tprm.models.vendor import Vendor
from src.cadence_tprm.services.questionnaire_service import QuestionnaireService
from src.cadence_tprm.services.risk_engine import RiskEngine
from src.cadence_tprm.services.workflow_engine import WorkflowEngine
from src.cadence_tprm.services.auth_service import get_current_user, require_tprm_admin

router = APIRouter(prefix="/assessments", tags=["Assessments"])

class ResponsesPayload(BaseModel):
    responses: Dict[str, str]

class ReviewPayload(BaseModel):
    group_name: str
    notes: str
    status: str = "Approved"

class DecisionPayload(BaseModel):
    decision_reason: str

@router.get("/{assessment_id}")
def get_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    assessment = db.query(Assessment).filter_by(id=assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")

    vendor = db.query(Vendor).filter_by(id=assessment.vendor_id).first()
    responses_map = {r.question_code: r.response_value for r in assessment.responses}
    template_data = QuestionnaireService.get_template_details(db, assessment.template_code, responses_map)

    return {
        "assessment": {
            "id": assessment.id,
            "vendor_id": assessment.vendor_id,
            "vendor_name": vendor.name if vendor else "",
            "vendor_tier": vendor.vendor_tier if vendor else "",
            "vendor_category": vendor.vendor_category if vendor else "",
            "template_code": assessment.template_code,
            "status": assessment.status,
            "overall_score": assessment.overall_score,
            "due_date": assessment.due_date.isoformat() if assessment.due_date else None,
            "submitted_at": assessment.submitted_at.isoformat() if assessment.submitted_at else None,
            "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
            "decision_reason": assessment.decision_reason,
            "decision_by": assessment.decision_by,
        },
        "responses": responses_map,
        "template": template_data,
        "findings": [
            {
                "id": f.id,
                "rule_code": f.rule_code,
                "risk_name": f.risk_name,
                "inherent_risk": f.inherent_risk,
                "control_id": f.control_id,
                "control_name": f.control_name,
                "responsible_group": f.responsible_group,
                "status": f.status,
                "mitigation_recommendation": f.mitigation_recommendation,
                "due_date": f.due_date.isoformat() if f.due_date else None,
            }
            for f in assessment.findings
        ],
        "reviews": [
            {
                "id": rev.id,
                "user_group_name": rev.user_group_name,
                "reviewer_email": rev.reviewer_email,
                "status": rev.status,
                "notes": rev.notes,
                "reviewed_at": rev.reviewed_at.isoformat() if rev.reviewed_at else None,
            }
            for rev in assessment.reviews
        ]
    }

@router.post("/{assessment_id}/responses")
def save_responses(
    assessment_id: str,
    payload: ResponsesPayload,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    QuestionnaireService.save_responses(db, assessment_id, payload.responses)
    return {"status": "saved", "count": len(payload.responses)}

@router.post("/{assessment_id}/submit")
def submit_assessment(
    assessment_id: str,
    payload: ResponsesPayload,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    assessment = db.query(Assessment).filter_by(id=assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")

    if assessment.status in ["Approved", "Rejected"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assessment is already finalized.")

    # 1. Save all incoming responses
    QuestionnaireService.save_responses(db, assessment_id, payload.responses)

    # 2. Validate all required questions answered
    all_responses = {r.question_code: r.response_value for r in assessment.responses}
    QuestionnaireService.validate_responses_for_submission(db, assessment, all_responses)

    # 3. Execute Risk Rules QR.1 to QR.90
    from datetime import datetime, timezone
    assessment.submitted_at = datetime.now(timezone.utc)
    findings, score, is_t3_auto_approve = RiskEngine.evaluate_assessment_submission(
        db, assessment, all_responses, actor_email=current_user["email"]
    )

    vendor = db.query(Vendor).filter_by(id=assessment.vendor_id).first()

    # 4. Handle Tier 3 Auto-Approval (WR.T3.3 / QR.73)
    if is_t3_auto_approve:
        WorkflowEngine.approve_vendor(
            db, vendor, assessment,
            actor_email="system@cadence.com",
            reason="Tier 3 automated approval: all questionnaire responses favorable (QR.73)."
        )
        return {
            "status": "auto_approved",
            "overall_score": score,
            "findings_count": len(findings),
            "message": "Tier 3 Vendor Auto-Approved under Rule WR.T3.3."
        }

    # Otherwise advance stage to In Review
    assessment.status = "In Review"
    vendor.lifecycle_status = "In Progress"
    db.commit()

    return {
        "status": "submitted_for_review",
        "overall_score": score,
        "findings_count": len(findings),
        "message": "Assessment submitted. Departmental review tasks generated."
    }

@router.post("/{assessment_id}/reviews")
def add_review(
    assessment_id: str,
    payload: ReviewPayload,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    assessment = db.query(Assessment).filter_by(id=assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")

    review = AssessmentReview(
        assessment_id=assessment_id,
        user_group_name=payload.group_name,
        reviewer_email=current_user["email"],
        status=payload.status,
        notes=payload.notes
    )
    db.add(review)
    db.commit()
    return {"status": "review_recorded"}

@router.post("/{assessment_id}/approve")
def approve_assessment(
    assessment_id: str,
    payload: DecisionPayload,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_tprm_admin)
):
    assessment = db.query(Assessment).filter_by(id=assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")

    vendor = db.query(Vendor).filter_by(id=assessment.vendor_id).first()
    WorkflowEngine.approve_vendor(db, vendor, assessment, actor_email=current_user["email"], reason=payload.decision_reason)

    return {"status": "approved", "vendor_id": vendor.id, "lifecycle_status": "Live"}

@router.post("/{assessment_id}/reject")
def reject_assessment(
    assessment_id: str,
    payload: DecisionPayload,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_tprm_admin)
):
    assessment = db.query(Assessment).filter_by(id=assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")

    vendor = db.query(Vendor).filter_by(id=assessment.vendor_id).first()
    WorkflowEngine.reject_vendor(db, vendor, assessment, actor_email=current_user["email"], reason=payload.decision_reason)

    return {"status": "rejected", "vendor_id": vendor.id, "lifecycle_status": "Review Reject"}
