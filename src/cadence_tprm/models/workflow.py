"""Workflow definitions, rules, SLA configs, instances, and transition history models.

Source Authority: Cadence_TPRM_Training.docx Section 4.2, 5.1, 6.4, Appendix A, Appendix D.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON
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
    status = Column(String(30), nullable=False, default="Published")  # Published or Draft
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    stages = Column(JSON, nullable=True, default=list)  # Ordered list of stage objects
    created_by = Column(String(150), nullable=False, default="Siddharth Gaikwad")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    instances = relationship("WorkflowInstance", back_populates="workflow", cascade="all, delete-orphan")

class WorkflowRuleSpec(Base):
    """Authoritative Appendix A workflow and automation rule definitions (WR.* and AR.*)."""
    __tablename__ = "workflow_rule_specs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    rule_code = Column(String(30), unique=True, nullable=False, index=True)  # e.g. WR.RP.1, WR.ON.1, AR.T1.1
    source_sr_no = Column(String(30), nullable=False)  # Preserves exact source SR. NO. (e.g. PWR.RP.4)
    rule_name = Column(String(150), nullable=False)
    workflow_name = Column(String(150), nullable=False, index=True)
    stage_name = Column(String(100), nullable=False)
    trigger_name = Column(String(100), nullable=True)
    trigger_type = Column(String(100), nullable=True)
    rule_type = Column(String(50), nullable=False)  # Workflow Rule, Stage Rule, Vendor Automation Rule
    description = Column(Text, nullable=False)
    condition_expression = Column(Text, nullable=False)
    action_expression = Column(Text, nullable=False)
    discrepancy_note = Column(Text, nullable=True)

class SLAConfig(Base):
    """Authoritative Appendix D SLA and Timeline definitions (SLA.1 to SLA.7)."""
    __tablename__ = "sla_configs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    sla_no = Column(String(20), unique=True, nullable=False, index=True)  # SLA.1 to SLA.7
    sla_name = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    timeline_days = Column(Integer, nullable=False)
    effective_deadline_days = Column(Integer, nullable=False)  # e.g. 5+4=9, 10+4=14, 15+4=19
    reminder_days = Column(Integer, nullable=True)  # None for SLA.6 and SLA.7

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
