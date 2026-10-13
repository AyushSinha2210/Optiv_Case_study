"""Vendor and Contract models with strict Table 9 attributes and lifecycle states.

Source Authority: Cadence_TPRM_Training.docx Section 2.1, 4.1, 5.2, Table 4, Table 9.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from src.cadence_tprm.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Vendor(Base):
    """Authoritative Vendor Record with Table 9 Attributes:

    1. Name: Third-party name
    2. Type: Consulting, Operations, Regulatory, Strategic, Technology, Unknown
    3. Criticality: Critical, High, Medium, Low
    4. Primary vendor contact: Email ID of vendor POC
    5. Business Owner: Email ID of internal POC
    6. Vendor Tier: Tier 1, Tier 2, Tier 3
    7. Vendor Category: Service Provider and Vendor, Revenue Partner, Marketing Partner,
                        Staffing Vendor, International Vendor
    8. Website: Domain of vendor organization
    """
    __tablename__ = "vendors"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    
    # Table 9 Required Attributes
    name = Column(String(255), nullable=False, index=True)
    type = Column(String(50), nullable=False, default="Technology")
    criticality = Column(String(50), nullable=False, default="Medium")
    primary_vendor_contact = Column(String(255), nullable=False, index=True)
    business_owner = Column(String(255), nullable=False, index=True)
    vendor_tier = Column(String(50), nullable=False, default="Tier 2", index=True)
    vendor_category = Column(String(100), nullable=False, default="Service Provider and Vendor", index=True)
    website = Column(String(255), nullable=True)

    # Lifecycle & FSM State
    # Lifecycle Status: New, In Progress, Live, Review Reject, Offboarding, Closed
    lifecycle_status = Column(String(50), nullable=False, default="New", index=True)
    current_workflow_name = Column(String(100), nullable=True)
    current_stage = Column(String(100), nullable=False, default="New Third Party")
    
    # Reassessment Dates & Lead time triggers
    last_assessment_completion_date = Column(DateTime, nullable=True)
    next_reassessment_due_date = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    contracts = relationship("Contract", back_populates="vendor", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="vendor", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="vendor", cascade="all, delete-orphan")
    findings = relationship("RiskFinding", back_populates="vendor", cascade="all, delete-orphan")

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    vendor_id = Column(String(36), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    contract_reference = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    source = Column(String(50), nullable=False, default="Ironclad")
    status = Column(String(50), nullable=False, default="Executed")
    effective_date = Column(Date, nullable=True)
    expiration_date = Column(Date, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    vendor = relationship("Vendor", back_populates="contracts")
