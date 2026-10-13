"""Security tests for controlled artifact access and path traversal defenses."""

import pytest
from pathlib import Path
from src.pii_guard.orchestration.artifacts import ArtifactManager
from src.pii_guard.orchestration.errors import ArtifactAccessError


def test_artifact_access_granted_when_authorized(tmp_path):
    """Artifact is retrievable when release_allowed is True and document_id matches."""
    mgr = ArtifactManager(storage_dir=tmp_path)
    doc_id = "doc-auth-100"
    token = mgr.store_artifact(doc_id, "Sanitized content for authorized release")

    resolved_path = mgr.validate_and_resolve_path(token, doc_id, release_allowed=True)
    assert resolved_path.is_file()
    assert resolved_path.read_text(encoding="utf-8") == "Sanitized content for authorized release"


def test_artifact_access_denied_when_release_blocked(tmp_path):
    """Artifact access is strictly forbidden when release_allowed is False."""
    mgr = ArtifactManager(storage_dir=tmp_path)
    doc_id = "doc-blocked-200"
    token = mgr.store_artifact(doc_id, "Residual PII present")

    with pytest.raises(ArtifactAccessError, match="release was blocked or withheld"):
        mgr.validate_and_resolve_path(token, doc_id, release_allowed=False)


def test_artifact_access_denied_on_document_mismatch(tmp_path):
    """Session cross-contamination: client with wrong document_id cannot access artifact."""
    mgr = ArtifactManager(storage_dir=tmp_path)
    token = mgr.store_artifact("doc-user-A", "User A document")

    with pytest.raises(ArtifactAccessError, match="does not belong to the authorized document"):
        mgr.validate_and_resolve_path(token, "doc-user-B", release_allowed=True)


@pytest.mark.parametrize("traversal_token", [
    "../secret.txt",
    "..\\secret.txt",
    "/etc/passwd",
    "C:\\Windows\\System32\\cmd.exe",
    "art-123\x00malicious",
    "art-123/../../etc/passwd",
    "",
])
def test_path_traversal_tokens_rejected(tmp_path, traversal_token):
    """Path traversal sequences in artifact tokens are immediately intercepted and rejected."""
    mgr = ArtifactManager(storage_dir=tmp_path)
    with pytest.raises(ArtifactAccessError, match="Malicious or invalid artifact reference token"):
        mgr.validate_and_resolve_path(traversal_token, "doc-test", release_allowed=True)


def test_nonexistent_artifact_token_fails(tmp_path):
    """Unguessable / missing artifact tokens fail closed."""
    mgr = ArtifactManager(storage_dir=tmp_path)
    with pytest.raises(ArtifactAccessError, match="Artifact not found"):
        mgr.validate_and_resolve_path("art-nonexistent12345", "doc-test", release_allowed=True)
