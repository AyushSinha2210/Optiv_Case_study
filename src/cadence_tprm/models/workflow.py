"""Workflow definitions, instances, and transition history models.

Source Authority: Cadence_TPRM_Training.docx Section 4.2, 5.1, 6.4, Appendix A, Tables 6, 7, 8, 10.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from src.cadence_tprm.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Workflow(Base):
    """Authoritative Workflows:

    1. CD_Onboarding Workflow
    2. CD_Revenue Partners Workflow
    3. CD_Marketing Partners Workflow
    4. CD_Service Providers Workflow
    5. CD_Staffing Vendors Workflow
    6. CD_International Vendors Workflow
    7. CD_Tier3 Workflow
    """
    __tablename__ = "workflows"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    instances = relationship("WorkflowInstance", back_populates="workflow", cascade="all, delete-orphan")

class WorkflowInstance(Base):
    __tablename__ = "workflow_instances"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    vendor_id = Column(String(36), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)
    current_stage = Column(String(100), nullable=False)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    workflow = relationship("Workflow", back_populates="instances")
    transitions = relationship("WorkflowTransition", back_populates="instance", cascade="all, delete-orphan")

class WorkflowTransition(Base):
    __tablename__ = "workflow_transitions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    instance_id = Column(String(36), ForeignKey("workflow_instances.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_email = Column(String(255), nullable=False)
    from_stage = Column(String(100), nullable=False)
    to_stage = Column(String(100), nullable=False)
    trigger_name = Column(String(100), nullable=False)  # e.g. On_T_Assign Workflow, RP_T_Assessment Approved
    rule_name = Column(String(100), nullable=True)  # e.g. WR.ON.1, WR.RP.3
    decision_reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    instance = relationship("WorkflowInstance", back_populates="transitions")
