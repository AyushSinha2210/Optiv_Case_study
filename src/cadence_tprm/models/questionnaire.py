"""Questionnaire templates, versions, sections, questions, conditional show logic, and risk rules.

Source Authority: Cadence_TPRM_Training.docx Section 6.3, Appendices B, C, E.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from src.cadence_tprm.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class QuestionnaireTemplate(Base):
    """Authoritative Templates from Appendix B:

    1. Due Diligence Questionnaire T1-2 v1 (Q.1)
    2. Due Diligence Questionnaire T3 v1 (Q.2)
    """
    __tablename__ = "questionnaire_templates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    questionnaire_no = Column(String(20), nullable=True, default="Q.1")
    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    template_language = Column(String(50), nullable=False, default="English")
    template_icon = Column(String(50), nullable=False, default="archive")
    source_file_name = Column(String(255), nullable=False, default="Final Due Diligence Questionnaire v1.0")
    approver_group = Column(String(100), nullable=False, default="Vendor Risk Management Group")
    version = Column(Integer, default=1, nullable=False)
    status = Column(String(30), nullable=False, default="Published")  # Draft, Published, Archived
    is_published = Column(Boolean, default=True, nullable=False)
    parent_template_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    sections = relationship(
        "QuestionnaireSection",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="QuestionnaireSection.order_index",
    )

class QuestionnaireSection(Base):
    """Authoritative 8 sections for T1-2 and 6 sections for T3."""
    __tablename__ = "questionnaire_sections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    template_id = Column(String(36), ForeignKey("questionnaire_templates.id", ondelete="CASCADE"), nullable=False)
    section_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    responsible_group = Column(String(100), nullable=False)  # e.g. Legal Group, Security Group
    order_index = Column(Integer, nullable=False, default=0)

    template = relationship("QuestionnaireTemplate", back_populates="sections")
    questions = relationship(
        "Question",
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="Question.order_index",
    )

class Question(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    section_id = Column(String(36), ForeignKey("questionnaire_sections.id", ondelete="CASCADE"), nullable=False)
    question_code = Column(String(50), nullable=False, index=True)  # e.g. 1.3, 4.11, 4.34
    prompt = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False, default="YesNo")  # YesNo, SingleChoice, MultiChoice, Text, Date
    options = Column(JSON, nullable=True)  # ["Yes", "No"] or ["0-5", "5-10", "10+"]
    favorable_answer = Column(String(100), nullable=True)  # Used for average scoring (QR.58 / QR.72) and QR.73 auto-approval
    is_required = Column(Boolean, default=True, nullable=False)
    is_conditional = Column(Boolean, default=False, nullable=False)  # Hidden by default until triggered
    order_index = Column(Integer, nullable=False, default=0)

    section = relationship("QuestionnaireSection", back_populates="questions")

class ConditionalRule(Base):
    """Authoritative show-logic rules from Appendix C (CL.1 to CL.14)."""
    __tablename__ = "conditional_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    rule_code = Column(String(50), unique=True, nullable=False, index=True)  # CL.1 to CL.14
    template_code = Column(String(100), nullable=False, index=True)
    section_name = Column(String(150), nullable=True)
    condition_logic = Column(String(20), nullable=False, default="Any")  # IF: Any / All
    trigger_question_code = Column(String(50), nullable=False)
    trigger_operator = Column(String(50), nullable=False, default="Equal To")
    trigger_response = Column(String(100), nullable=False)  # Yes, No
    primary_shown_question = Column(String(50), nullable=True)
    copy_logic_to_questions = Column(JSON, nullable=True, default=list)
    shown_question_codes = Column(JSON, nullable=False)  # Full list of revealed questions
    description = Column(Text, nullable=True)

class RiskRule(Base):
    """Authoritative questionnaire rules from Appendix E (QR.1 to QR.90)."""
    __tablename__ = "risk_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    rule_code = Column(String(50), unique=True, nullable=False, index=True)  # QR.1 to QR.90
    template_code = Column(String(100), nullable=False, index=True)
    rule_name = Column(String(255), nullable=False)
    condition_logic = Column(String(50), nullable=False, default="IF: Any")
    trigger_type = Column(String(50), nullable=False, default="Question")  # Question, Assessment Score, Scoring
    trigger_question_code = Column(String(150), nullable=False)
    trigger_operator = Column(String(50), nullable=False, default="Equal To")
    trigger_response = Column(String(150), nullable=False)
    action_type = Column(String(100), nullable=False, default="Create risk")
    risk_name = Column(String(255), nullable=True)
    inherent_risk = Column(String(50), nullable=True)  # High, Medium, Low
    control_id = Column(String(50), nullable=True)  # QRC_*
    control_name = Column(String(255), nullable=True)
    task_name = Column(String(255), nullable=True)
    assignee = Column(String(255), nullable=True)
    collaborator_group = Column(String(150), nullable=True)
    responsible_group = Column(String(100), nullable=True)
    result_status = Column(String(50), nullable=True)
    result_comments = Column(Text, nullable=True)
    source_notes = Column(Text, nullable=True)
