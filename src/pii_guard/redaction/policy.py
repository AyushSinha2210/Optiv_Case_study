"""Replacement policy for Contract B PII categories."""

from types import MappingProxyType
from typing import Mapping


DEFAULT_POLICY: Mapping[str, str] = MappingProxyType(
    {
        "PERSON": "[REDACTED_PERSON]",
        "NAME": "[REDACTED_PERSON]",
        "PERSON_NAME": "[REDACTED_PERSON]",
        "CANDIDATE_NAME": "[REDACTED_PERSON]",
        "FULL_NAME": "[REDACTED_PERSON]",
        "EMAIL": "[REDACTED_EMAIL]",
        "PHONE": "[REDACTED_PHONE]",
        "ADDRESS": "[REDACTED_ADDRESS]",
        "GOVERNMENT_ID": "[REDACTED_ID]",
        "FINANCIAL_IDENTIFIER": "[REDACTED_FINANCIAL]",
        "IP_ADDRESS": "[REDACTED_IP]",
        "EMPLOYEE_ID": "[REDACTED_EMPLOYEE_ID]",
    }
)



class PolicyError(ValueError):
    """Raised when a detector returns an unsupported category."""


def get_replacement(entity_type: str) -> str:
    """Return the approved token; unknown categories fail closed."""

    if not isinstance(entity_type, str) or not entity_type:
        raise PolicyError("PII category is missing")
    try:
        return DEFAULT_POLICY[entity_type.upper()]
    except KeyError as exc:
        raise PolicyError("Unsupported PII category") from exc
