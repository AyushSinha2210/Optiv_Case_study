"""Organizational hierarchy, user groups, users, and RBAC models.

Source Authority: Cadence_TPRM_Training.docx Section 2.3, 4.2, 6.1, Table 5.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import relationship
from src.cadence_tprm.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), unique=True, nullable=False)
    domain = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    departments = relationship("Department", back_populates="organization", cascade="all, delete-orphan")
    users = relationship("User", back_populates="organization")

class Department(Base):
    __tablename__ = "departments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    organization = relationship("Organization", back_populates="departments")

class UserGroup(Base):
    """Authoritative TPRM User Groups as defined in Table 5:

    - Vendor Risk Management Group (Admin & Edit)
    - Legal Group
    - Procurement Group
    - Finance Group
    - IT Group
    - Compliance Group
    - Privacy Group
    - Security Group
    - Data Quality Group
    """
    __tablename__ = "user_groups"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    default_permission = Column(String(20), nullable=False, default="Edit")  # Admin or Edit
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    memberships = relationship("GroupMembership", back_populates="group", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_tprm_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization", back_populates="users")
    memberships = relationship("GroupMembership", back_populates="user", cascade="all, delete-orphan")

class GroupMembership(Base):
    __tablename__ = "group_memberships"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(String(36), ForeignKey("user_groups.id", ondelete="CASCADE"), nullable=False)
    role_in_group = Column(String(20), nullable=False, default="Edit")  # Admin or Edit
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="memberships")
    group = relationship("UserGroup", back_populates="memberships")

    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="uq_user_group"),
    )
