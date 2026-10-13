"""Questionnaire templates, sections, questions, conditional show logic, and risk rules.

Source Authority: Cadence_TPRM_Training.docx Section 6.3, Appendices B, C, E, Tables 11, 12, 14.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from src.cadence_tprm.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class QuestionnaireTemplate(Base):
    """Authoritative Templates from Table 11:

    1. Due Diligence Questionnaire T1-2 v1
    2. Due Diligence Questionnaire T3 v1
    """
    __tablename__ = "questionnaire_templates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_published = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    sections = relationship("QuestionnaireSection", back_populates="template", cascade="all, delete-orphan", order_by="QuestionnaireSection.order_index")

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
    questions = relationship("Question", back_populates="section", cascade="all, delete-orphan", order_by="Question.order_index")

class Question(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    section_id = Column(String(36), ForeignKey("questionnaire_sections.id", ondelete="CASCADE"), nullable=False)
    question_code = Column(String(50), nullable=False, index=True)  # e.g. 1.3, 4.11, 4.34
    prompt = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False, default="YesNo")  # YesNo, SingleChoice, MultiChoice, Text, Link
    options = Column(JSON, nullable=True)  # ["Yes", "No"] or ["0-5", "5-10", "10+"]
    is_required = Column(Boolean, default=True, nullable=False)
    is_conditional = Column(Boolean, default=False, nullable=False)  # Hidden by default until triggered
    order_index = Column(Integer, nullable=False, default=0)

    section = relationship("QuestionnaireSection", back_populates="questions")

class ConditionalRule(Base):
    """Authoritative show-logic rules from Table 12 (CL.1 to CL.14)."""
    __tablename__ = "conditional_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    rule_code = Column(String(50), unique=True, nullable=False, index=True)  # e.g. CL.1, CL.5
    template_code = Column(String(100), nullable=False, index=True)
    trigger_question_code = Column(String(50), nullable=False)
    trigger_operator = Column(String(50), nullable=False, default="Equal To")
    trigger_response = Column(String(100), nullable=False)  # e.g. Yes, No
    shown_question_codes = Column(JSON, nullable=False)  # list of strings: ["1.6", "1.7", "1.8"]
    description = Column(Text, nullable=True)

class RiskRule(Base):
    """Authoritative risk scoring & task automation rules from Table 14 (QR.1 to QR.90)."""
    __tablename__ = "risk_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    rule_code = Column(String(50), unique=True, nullable=False, index=True)  # e.g. QR.1, QR.45
    template_code = Column(String(100), nullable=False, index=True)
    rule_name = Column(String(255), nullable=False)
    trigger_question_code = Column(String(50), nullable=False)
    trigger_operator = Column(String(50), nullable=False, default="Equal To")
    trigger_response = Column(String(100), nullable=False)  # e.g. Yes, No, 0-5
    action_type = Column(String(50), nullable=False, default="Create risk")  # Create risk or Create task
    risk_name = Column(String(255), nullable=True)
    inherent_risk = Column(String(50), nullable=True)  # High, Medium, Low
    control_id = Column(String(50), nullable=True)  # QRC_*
    control_name = Column(String(255), nullable=True)
    responsible_group = Column(String(100), nullable=True)
