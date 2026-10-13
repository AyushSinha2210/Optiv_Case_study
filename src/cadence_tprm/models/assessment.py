"""Assessment lifecycle, responses, findings, reviews, and mitigations.

Source Authority: Cadence_TPRM_Training.docx Section 4.2, 5.1, 6.3, Appendices B, E.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from src.cadence_tprm.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    vendor_id = Column(String(36), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)
    template_code = Column(String(100), nullable=False)
    respondent_email = Column(String(255), nullable=False)
    approver_group = Column(String(100), nullable=False, default="Vendor Risk Management Group")
    
    # Status: Draft, Submitted, In Review, Approved, Rejected
    status = Column(String(50), nullable=False, default="Draft", index=True)
    overall_score = Column(Float, nullable=True)  # Percentage score
    decision_reason = Column(Text, nullable=True)
    decision_by = Column(String(255), nullable=True)
    
    due_date = Column(DateTime, nullable=True)  # SLA.1 (9 days)
    submitted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    vendor = relationship("Vendor", back_populates="assessments")
    responses = relationship("QuestionResponse", back_populates="assessment", cascade="all, delete-orphan")
    findings = relationship("RiskFinding", back_populates="assessment", cascade="all, delete-orphan")
    reviews = relationship("AssessmentReview", back_populates="assessment", cascade="all, delete-orphan")

class QuestionResponse(Base):
    __tablename__ = "question_responses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    question_code = Column(String(50), nullable=False, index=True)
    response_value = Column(Text, nullable=False)
    evidence_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    assessment = relationship("Assessment", back_populates="responses")

    __table_args__ = (
        UniqueConstraint("assessment_id", "question_code", name="uq_assessment_question"),
    )

class RiskFinding(Base):
    """Inherent risk finding triggered by Appendix E rules."""
    __tablename__ = "risk_findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    vendor_id = Column(String(36), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_code = Column(String(50), nullable=False)
    risk_name = Column(String(255), nullable=False)
    inherent_risk = Column(String(50), nullable=False)  # High, Medium, Low
    control_id = Column(String(50), nullable=False)  # QRC_*
    control_name = Column(String(255), nullable=False)
    responsible_group = Column(String(100), nullable=False)
    
    # Status: Open, Acknowledged, Remediating, Accepted, Closed
    status = Column(String(50), nullable=False, default="Open", index=True)
    mitigation_recommendation = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=False)  # SLA.3 (9d), SLA.4 (14d), SLA.5 (19d)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    assessment = relationship("Assessment", back_populates="findings")
    vendor = relationship("Vendor", back_populates="findings")
    mitigation_plans = relationship("MitigationPlan", back_populates="finding", cascade="all, delete-orphan")

class AssessmentReview(Base):
    """Departmental review record by user group members."""
    __tablename__ = "assessment_reviews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_group_name = Column(String(100), nullable=False)
    reviewer_email = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="Pending")  # Pending, Approved, ConcernsRaised
    notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    assessment = relationship("Assessment", back_populates="reviews")

class MitigationPlan(Base):
    __tablename__ = "mitigation_plans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    finding_id = Column(String(36), ForeignKey("risk_findings.id", ondelete="CASCADE"), nullable=False)
    owner_email = Column(String(255), nullable=False)
    plan_description = Column(Text, nullable=False)
    target_completion_date = Column(DateTime, nullable=False)
    is_completed = Column(String(20), nullable=False, default="In Progress")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    finding = relationship("RiskFinding", back_populates="mitigation_plans")
