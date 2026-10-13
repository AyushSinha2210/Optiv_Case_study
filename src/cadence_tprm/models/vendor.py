"""Vendor, VendorAttributeDefinition, Contract, and RenewalDecision models.

Source Authority: Cadence_TPRM_Training.docx Section 2.1, 4.1, 5.2, 6.2, 18.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Date, JSON
from sqlalchemy.orm import relationship
from src.cadence_tprm.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Vendor(Base):
    """Authoritative Vendor Record with Section 5.2 Attributes:

    1. Name: Default system attribute representing the third-party name (Ironclad -> OneTrust)
    2. Type: Consulting, Operations, Regulatory, Strategic, Technology, Unknown
    3. Criticality: Critical, High, Medium, Low (optional, used for prioritization)
    4. Primary vendor contact: Mandatory email ID of vendor POC
    5. Business Owner: Email ID of internal POC
    6. Vendor Tier: Tier 1, Tier 2, Tier 3
    7. Vendor Category: Service Provider and Vendor, Revenue Partner, Marketing Partner,
                        Staffing Vendor, International Vendor
    8. Website: Domain of vendor organization
    """
    __tablename__ = "vendors"

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # Section 5.2 Attributes
    name = Column(String(255), nullable=False, index=True)
    type = Column(String(50), nullable=False, default="Technology")
    criticality = Column(String(50), nullable=True, default="Medium")
    primary_vendor_contact = Column(String(255), nullable=False, index=True)
    business_owner = Column(String(255), nullable=False, index=True)
    vendor_tier = Column(String(50), nullable=False, default="Tier 2", index=True)
    vendor_category = Column(String(100), nullable=False, default="Service Provider and Vendor", index=True)
    website = Column(String(255), nullable=True)
    custom_attributes = Column(JSON, nullable=True, default=dict)

    # Lifecycle & FSM State
    # Lifecycle Status: New, In Progress, Live, Review Reject, Offboarding, Closed, Archived
    lifecycle_status = Column(String(50), nullable=False, default="New", index=True)
    current_workflow_name = Column(String(100), nullable=True)
    current_stage = Column(String(100), nullable=False, default="New Third Party")
    is_archived = Column(Boolean, default=False, nullable=False)

    # Reassessment Dates & Lead time triggers
    last_assessment_completion_date = Column(DateTime, nullable=True)
    next_reassessment_due_date = Column(DateTime, nullable=True)
    renewal_status = Column(String(50), nullable=True, default="Active")

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    contracts = relationship("Contract", back_populates="vendor", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="vendor", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="vendor", cascade="all, delete-orphan")
    findings = relationship("RiskFinding", back_populates="vendor", cascade="all, delete-orphan")
    renewals = relationship("RenewalDecision", back_populates="vendor", cascade="all, delete-orphan")

class VendorAttributeDefinition(Base):
    """Section 6.2 Attribute Manager inventory record."""
    __tablename__ = "vendor_attribute_definitions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    key_name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    description_key = Column(Text, nullable=False)
    response_type = Column(String(50), nullable=False, default="Single select")  # Single select, Text, Email, URL
    options = Column(JSON, nullable=True, default=list)  # Permitted values
    source = Column(String(50), nullable=False, default="System")  # System or Custom
    direction = Column(String(100), nullable=False, default="From: Ironclad To: OneTrust")
    is_mandatory = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_workflow_driver = Column(Boolean, default=False, nullable=False)
    last_reviewed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

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

class RenewalDecision(Base):
    """Section 18: Tracks formal vendor renewal decisions informed by reassessment outcomes."""
    __tablename__ = "renewal_decisions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    vendor_id = Column(String(36), ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=True)
    contract_id = Column(String(36), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=True)
    decision = Column(String(50), nullable=False, default="Pending")  # Pending, Renewed, Conditional Renewal, Non-Renewal / Offboard
    decided_by = Column(String(255), nullable=True)
    rationale = Column(Text, nullable=True)
    open_findings_at_decision = Column(String(20), nullable=True, default="0")
    next_renewal_date = Column(Date, nullable=True)
    decided_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    vendor = relationship("Vendor", back_populates="renewals")
