"""Organizational hierarchy, departments, user groups, users, roles, and permissions models.

Hierarchy:
Organization -> Departments -> Groups -> Users -> Assigned roles -> Permissions

Source Authority: Cadence_TPRM_Training.docx Section 2.3, 4.2, 6.1, Table 5.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UniqueConstraint, Text, JSON
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
    groups = relationship("UserGroup", back_populates="department")

class Role(Base):
    """Enterprise Role definition (e.g., TPRM Administrator, VRM Reviewer, Department Reviewer, Respondent)."""
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(60), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(JSON, nullable=False, default=list)  # list of permission codes
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Permission(Base):
    """Granular action/resource permission."""
    __tablename__ = "permissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(80), unique=True, nullable=False, index=True)
    resource = Column(String(60), nullable=False)
    action = Column(String(60), nullable=False)
    description = Column(Text, nullable=True)

class UserGroup(Base):
    """Authoritative TPRM User Groups as defined in Section 4.2:

    - Vendor Risk Management Group (Admin & Edit)
    - Legal Group (Edit)
    - Procurement Group (Edit)
    - Finance Group (Edit)
    - IT Group (Edit)
    - Compliance Group (Edit)
    - Privacy Group (Edit)
    - Security Group (Edit)
    - Data Quality Group (Edit)
    """
    __tablename__ = "user_groups"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    default_permission = Column(String(20), nullable=False, default="Edit")  # Admin or Edit
    review_sections = Column(JSON, nullable=True)  # Questionnaire sections assigned to this group
    last_reviewed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    department = relationship("Department", back_populates="groups")
    memberships = relationship("GroupMembership", back_populates="group", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    title = Column(String(150), nullable=True)
    hashed_password = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_tprm_admin = Column(Boolean, default=False, nullable=False)
    is_synthetic = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization", back_populates="users")
    memberships = relationship("GroupMembership", back_populates="user", cascade="all, delete-orphan")

class GroupMembership(Base):
    __tablename__ = "group_memberships"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(String(36), ForeignKey("user_groups.id", ondelete="CASCADE"), nullable=False)
    role_in_group = Column(String(20), nullable=False, default="Edit")  # Admin or Edit
    role_code = Column(String(60), nullable=True, default="REVIEWER")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="memberships")
    group = relationship("UserGroup", back_populates="memberships")

    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="uq_user_group"),
    )
