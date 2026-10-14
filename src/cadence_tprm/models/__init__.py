"""Export all SQLAlchemy models for clean declarative registration."""

from src.cadence_tprm.database import Base
from src.cadence_tprm.models.identity import (
    Organization,
    Department,
    Role,
    Permission,
    UserGroup,
    User,
    GroupMembership,
)
from src.cadence_tprm.models.vendor import (
    Vendor,
    VendorAttributeDefinition,
    Contract,
    RenewalDecision,
)
from src.cadence_tprm.models.questionnaire import (
    QuestionnaireTemplate,
    QuestionnaireSection,
    Question,
    ConditionalRule,
    RiskRule,
)
from src.cadence_tprm.models.assessment import (
    Assessment,
    QuestionResponse,
    RiskFinding,
    AssessmentReview,
    MitigationPlan,
)
from src.cadence_tprm.models.workflow import (
    Workflow,
    WorkflowRuleSpec,
    SLAConfig,
    WorkflowInstance,
    WorkflowTransition,
)
from src.cadence_tprm.models.task import (
    Task,
    Notification,
)
from src.cadence_tprm.models.audit import (
    AuditLog,
)

__all__ = [
    "Base",
    "Organization",
    "Department",
    "Role",
    "Permission",
    "UserGroup",
    "User",
    "GroupMembership",
    "Vendor",
    "VendorAttributeDefinition",
    "Contract",
    "RenewalDecision",
    "QuestionnaireTemplate",
    "QuestionnaireSection",
    "Question",
    "ConditionalRule",
    "RiskRule",
    "Assessment",
    "QuestionResponse",
    "RiskFinding",
    "AssessmentReview",
    "MitigationPlan",
    "Workflow",
    "WorkflowRuleSpec",
    "SLAConfig",
    "WorkflowInstance",
    "WorkflowTransition",
    "Task",
    "Notification",
    "AuditLog",
]
