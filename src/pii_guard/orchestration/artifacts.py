"""Controlled artifact storage and retrieval manager.

SECURITY & ACCESS RULES:
1. Web clients and users NEVER receive direct filesystem paths.
2. Artifacts are identified by opaque, unguessable tokens (e.g. art-<uuid>).
3. Retrieval strictly verifies that the artifact belongs to the authorized document and was RELEASED.
4. Path traversal attempts (.., /, \\, null bytes) are strictly blocked with ArtifactAccessError.
"""

import os
import uuid
import tempfile
from pathlib import Path
from typing import Dict, Optional, Union
from pydantic import BaseModel, Field, ConfigDict

from .errors import ArtifactAccessError


class ArtifactEntry(BaseModel):
    """Metadata record for a protected stored artifact."""
    model_config = ConfigDict(extra="forbid")

    artifact_ref: str
    document_id: str
    file_path: str
    content_type: str
    file_size_bytes: int
    created_at_utc: str


class ArtifactManager:
    """Sandbox storage manager enforcing release gate access controls on artifacts."""

    def __init__(self, storage_dir: Optional[Union[Path, str]] = None):
        if storage_dir is not None:
            self._temp_dir = Path(storage_dir)
        else:
            self._temp_dir = Path(tempfile.mkdtemp(prefix="pii_guard_artifacts_"))
        self._temp_dir.mkdir(parents=True, exist_ok=True)
        self._registry: Dict[str, ArtifactEntry] = {}

    @property
    def storage_dir(self) -> Path:
        return self._temp_dir

    def store_artifact(
        self,
        document_id: str,
        content: Union[str, bytes],
        file_extension: str = "txt",
        content_type: str = "text/plain",
    ) -> str:
        """Securely persist a redacted artifact and return an opaque reference token."""
        clean_ext = file_extension.lstrip(".")
        token = f"art-{uuid.uuid4().hex}"
        safe_filename = f"{token}.{clean_ext}"
        target_path = (self._temp_dir / safe_filename).resolve()

        # Guard against sandbox breakout
        if not str(target_path).startswith(str(self._temp_dir.resolve())):
            raise ArtifactAccessError("Attempted sandbox path breakout during storage")

        if isinstance(content, str):
            target_path.write_text(content, encoding="utf-8")
            size = len(content.encode("utf-8"))
        else:
            target_path.write_bytes(content)
            size = len(content)

        import datetime
        self._registry[token] = ArtifactEntry(
            artifact_ref=token,
            document_id=document_id,
            file_path=str(target_path),
            content_type=content_type,
            file_size_bytes=size,
            created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        return token

    def validate_and_resolve_path(
        self,
        artifact_ref: str,
        authorized_document_id: str,
        release_allowed: bool,
    ) -> Path:
        """Validate ownership and release gate permission, returning safe local Path."""
        # 1. Defend against path traversal in the token itself
        if not artifact_ref or any(char in artifact_ref for char in ["..", "/", "\\", "\x00", ":"]):
            raise ArtifactAccessError("Malicious or invalid artifact reference token")

        # 2. Enforce release gate permission
        if not release_allowed:
            raise ArtifactAccessError(
                "Access denied: Artifact release was blocked or withheld by the verification gate"
            )

        # 3. Lookup in internal registry
        entry = self._registry.get(artifact_ref)
        if not entry:
            raise ArtifactAccessError("Artifact not found or has expired")

        # 4. Verify document ID ownership
        if entry.document_id != authorized_document_id:
            raise ArtifactAccessError("Artifact does not belong to the authorized document session")

        path = Path(entry.file_path).resolve()

        # 5. Verify sandbox containment
        if not str(path).startswith(str(self._temp_dir.resolve())):
            raise ArtifactAccessError("Path traversal violation detected")

        if not path.is_file():
            raise ArtifactAccessError("Artifact file missing on server storage")

        return path

    def read_artifact_bytes(
        self,
        artifact_ref: str,
        authorized_document_id: str,
        release_allowed: bool,
    ) -> bytes:
        """Retrieve artifact binary content following release authorization check."""
        path = self.validate_and_resolve_path(artifact_ref, authorized_document_id, release_allowed)
        return path.read_bytes()

    def cleanup(self) -> None:
        """Remove all stored artifacts in this sandbox."""
        for entry in self._registry.values():
            try:
                p = Path(entry.file_path)
                if p.is_file():
                    p.unlink(missing_ok=True)
            except Exception:
                pass
        self._registry.clear()


# Default singleton manager for standard runs
_DEFAULT_ARTIFACT_MANAGER = ArtifactManager()


def get_default_artifact_manager() -> ArtifactManager:
    return _DEFAULT_ARTIFACT_MANAGER
