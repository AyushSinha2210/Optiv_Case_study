"""Fail-closed release decision."""


def evaluate_release(
    *,
    redaction_succeeded: bool,
    text_verification_status: str,
    artifact_verification_status: str,
    structure_status: str,
) -> dict[str, object]:
    """Approve only when every mandatory check explicitly passes."""

    if redaction_succeeded is not True:
        return {"status": "ERROR", "release_allowed": False, "reason_code": "REDACTION_FAILED"}
    if text_verification_status != "PASS":
        return {"status": "BLOCKED", "release_allowed": False, "reason_code": "TEXT_VERIFICATION_FAILED"}
    if artifact_verification_status != "PASS":
        return {"status": "BLOCKED", "release_allowed": False, "reason_code": "ARTIFACT_VERIFICATION_NOT_PASSED"}
    if structure_status != "PASS":
        return {"status": "BLOCKED", "release_allowed": False, "reason_code": "STRUCTURE_VERIFICATION_NOT_PASSED"}
    return {"status": "PASS", "release_allowed": True, "reason_code": "ALL_REQUIRED_CHECKS_PASSED"}
