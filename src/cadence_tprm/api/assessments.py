"""Assessment submission, response drafting, risk evaluation, findings management, and approval/rejection endpoints."""

from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.cadence_tprm.database import get_db
from src.cadence_tprm.models.assessment import Assessment, AssessmentReview, RiskFinding, MitigationPlan
from src.cadence_tprm.models.vendor import Vendor
from src.cadence_tprm.services.questionnaire_service import QuestionnaireService
from src.cadence_tprm.services.risk_engine import RiskEngine
from src.cadence_tprm.services.workflow_engine import WorkflowEngine
from src.cadence_tprm.services.audit_service import AuditService
from src.cadence_tprm.services.auth_service import get_current_user, require_tprm_admin

router = APIRouter(prefix="/assessments", tags=["Assessments"])

class ResponsesPayload(BaseModel):
    responses: Dict[str, str] = {}

class LaunchAssessmentPayload(BaseModel):
    vendor_id: str
    template_code: Optional[str] = None

class ReviewPayload(BaseModel):
    group_name: Optional[str] = None
    user_group_name: Optional[str] = None
    notes: str = ""
    status: str = "Approved"

class DecisionPayload(BaseModel):
    decision_reason: str

class FindingUpdatePayload(BaseModel):
    status: str
    mitigation_recommendation: Optional[str] = None
    plan_description: Optional[str] = None

@router.get("")
def list_assessments(
    vendor_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(Assessment)
    if vendor_id:
        query = query.filter_by(vendor_id=vendor_id)
    if status_filter:
        query = query.filter_by(status=status_filter)

    assessments = query.order_by(Assessment.created_at.desc()).all()
    items = []
    for a in assessments:
        vendor = db.query(Vendor).filter_by(id=a.vendor_id).first()
        findings_count = db.query(RiskFinding).filter_by(assessment_id=a.id).count()
        items.append({
            "id": a.id,
            "vendor_id": a.vendor_id,
            "vendor_name": vendor.name if vendor else "Unknown Vendor",
            "vendor_tier": vendor.vendor_tier if vendor else "",
            "vendor_category": vendor.vendor_category if vendor else "",
            "template_code": a.template_code,
            "respondent_email": a.respondent_email,
            "approver_group": a.approver_group,
            "status": a.status,
            "overall_score": a.overall_score,
            "findings_count": findings_count,
            "due_date": a.due_date.isoformat() if a.due_date else None,
            "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
            "completed_at": a.completed_at.isoformat() if a.completed_at else None,
            "decision_reason": a.decision_reason,
            "decision_by": a.decision_by,
        })
    return {"items": items, "assessments": items, "total": len(items)}

@router.post("", status_code=status.HTTP_201_CREATED)
def launch_assessment(
    payload: LaunchAssessmentPayload,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    vendor = db.query(Vendor).filter_by(id=payload.vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found.")

    t_code = payload.template_code or ("T3_v1" if vendor.vendor_tier == "Tier 3" else "T1-2_v1")
    now = datetime.now(timezone.utc)
    asm = Assessment(
        vendor_id=vendor.id,
        template_code=t_code,
        respondent_email=vendor.primary_vendor_contact,
        approver_group="Vendor Risk Management Group",
        status="Draft",
        due_date=now + timedelta(days=9),
    )
    db.add(asm)
    db.flush()

    AuditService.log_event(
        db,
        actor_email=current_user["email"],
        action="ASSESSMENT_LAUNCHED",
        entity_type="ASSESSMENT",
        entity_id=asm.id,
        details={"vendor_id": vendor.id, "vendor_name": vendor.name, "template_code": t_code}
    )
    db.commit()
    return {"status": "launched", "assessment_id": asm.id, "template_code": t_code}

@router.get("/findings/all")
def list_all_findings(
    severity: Optional[str] = None,
    status_filter: Optional[str] = None,
    group: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(RiskFinding)
    if severity and severity != "All":
        query = query.filter_by(inherent_risk=severity)
    if status_filter and status_filter != "All":
        query = query.filter_by(status=status_filter)
    if group and group != "All":
        query = query.filter_by(responsible_group=group)

    findings = query.order_by(RiskFinding.created_at.desc()).all()
    items = []
    for f in findings:
        v = db.query(Vendor).filter_by(id=f.vendor_id).first()
        items.append({
            "id": f.id,
            "assessment_id": f.assessment_id,
            "vendor_id": f.vendor_id,
            "vendor_name": v.name if v else "Vendor",
            "rule_code": f.rule_code,
            "risk_name": f.risk_name,
            "inherent_risk": f.inherent_risk,
            "control_id": f.control_id,
            "control_name": f.control_name,
            "responsible_group": f.responsible_group,
            "status": f.status,
            "mitigation_recommendation": f.mitigation_recommendation,
            "due_date": f.due_date.isoformat() if f.due_date else None,
            "acknowledged_at": f.acknowledged_at.isoformat() if f.acknowledged_at else None,
            "resolved_at": f.resolved_at.isoformat() if f.resolved_at else None,
        })
    return {"items": items, "findings": items, "total": len(items)}

@router.put("/findings/{finding_id}")
def update_finding(
    finding_id: str,
    payload: FindingUpdatePayload,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    finding = db.query(RiskFinding).filter_by(id=finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Risk finding not found.")

    old_status = finding.status
    finding.status = payload.status
    now = datetime.now(timezone.utc)
    if payload.status == "Acknowledged" and not finding.acknowledged_at:
        finding.acknowledged_at = now
    if payload.status == "Closed":
        finding.resolved_at = now

    if payload.mitigation_recommendation is not None:
        finding.mitigation_recommendation = payload.mitigation_recommendation

    if payload.plan_description:
        db.add(MitigationPlan(
            finding_id=finding.id,
            owner_email=current_user["email"],
            plan_description=payload.plan_description,
            target_completion_date=now + timedelta(days=30),
            is_completed="Completed" if payload.status == "Closed" else "In Progress",
        ))

    AuditService.log_event(
        db,
        actor_email=current_user["email"],
        action="RISK_FINDING_UPDATED",
        entity_type="ASSESSMENT",
        entity_id=finding.assessment_id,
        details={
            "finding_id": finding.id,
            "rule_code": finding.rule_code,
            "old_status": old_status,
            "new_status": finding.status,
            "mitigation_recommendation": finding.mitigation_recommendation,
        }
    )
    db.commit()
    return {
        "status": "updated",
        "finding": {
            "id": finding.id,
            "status": finding.status,
            "mitigation_recommendation": finding.mitigation_recommendation,
        }
    }

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
    payload: Optional[ResponsesPayload] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    assessment = db.query(Assessment).filter_by(id=assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")

    if assessment.status in ["Approved", "Rejected"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assessment is already finalized.")

    if payload and payload.responses:
        QuestionnaireService.save_responses(db, assessment_id, payload.responses)

    all_responses = {r.question_code: r.response_value for r in assessment.responses}
    QuestionnaireService.validate_responses_for_submission(db, assessment, all_responses)

    assessment.submitted_at = datetime.now(timezone.utc)
    findings, score, is_t3_auto_approve = RiskEngine.evaluate_assessment_submission(
        db, assessment, all_responses, actor_email=current_user["email"]
    )

    vendor = db.query(Vendor).filter_by(id=assessment.vendor_id).first()

    # Handle Tier 3 Auto-Approval (WR.T3.3 / QR.73)
    if is_t3_auto_approve:
        WorkflowEngine.approve_vendor(
            db, vendor, assessment,
            actor_email="system@cadence.com",
            reason="The third-party is Approved"
        )
        return {
            "status": "auto_approved",
            "overall_score": score,
            "findings_count": len(findings),
            "result_comments": "The third-party is Approved",
            "message": "Tier 3 Vendor Auto-Approved under Rule QR.73 / WR.T3.3 ('The third-party is Approved')."
        }

    assessment.status = "In Review"
    vendor.lifecycle_status = "In Progress"
    db.commit()

    return {
        "status": "submitted_for_review",
        "overall_score": score,
        "findings_count": len(findings),
        "message": "Assessment submitted. Risk rules QR.1-QR.90 evaluated and departmental review tasks generated."
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

    grp = payload.group_name or payload.user_group_name or (current_user.get("groups") or ["Vendor Risk Management Group"])[0]
    review = AssessmentReview(
        assessment_id=assessment_id,
        user_group_name=grp,
        reviewer_email=current_user["email"],
        status=payload.status,
        notes=payload.notes
    )
    db.add(review)
    AuditService.log_event(
        db,
        actor_email=current_user["email"],
        action="DEPARTMENTAL_REVIEW_RECORDED",
        entity_type="ASSESSMENT",
        entity_id=assessment_id,
        details={"group_name": grp, "status": payload.status, "notes": payload.notes}
    )
    db.commit()
    return {"status": "review_recorded", "group_name": grp}

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

    return {"status": "rejected", "vendor_id": vendor.id, "lifecycle_status": "Review Reject", "stage": vendor.current_stage}
