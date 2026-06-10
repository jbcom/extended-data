"""Webhook handler for Meshy API callbacks."""

from __future__ import annotations

import hashlib

from datetime import datetime, timezone
from typing import Any

from extended_data.connectors.meshy import base
from extended_data.connectors.meshy.webhooks.schemas import MeshyWebhookPayload

from ..persistence.repository import TaskRepository
from ..persistence.schemas import ArtifactRecord


def _utc_now() -> datetime:
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)


class WebhookHandler:
    """Handle webhook callbacks from Meshy API.

    This class processes webhook payloads, updates task state in the repository,
    and downloads artifacts on successful completion.
    """

    def __init__(
        self,
        repository: TaskRepository,
        download_artifacts: bool = True,
    ):
        """Initialize webhook handler.

        Args:
            repository: TaskRepository for updating state
            download_artifacts: Whether to download GLB files on SUCCEEDED
        """
        self.repository = repository
        self.download_artifacts = download_artifacts

    def handle_webhook(
        self, payload: MeshyWebhookPayload, project: str | None = None, spec_hash: str | None = None
    ) -> dict[str, Any]:
        """Process webhook payload and update repository.

        Args:
            payload: Parsed webhook payload
            project: Optional project name (will search if not provided)
            spec_hash: Optional spec hash (will search if not provided)

        Returns:
            Dict with status and details
        """
        task_lookup = self.repository.find_task_by_id(task_id=payload.id, project=project)

        if not task_lookup:
            return {
                "status": "error",
                "message": f"Task {payload.id} not found in repository",
                "task_id": payload.id,
            }

        found_project, found_spec_hash, asset_manifest = task_lookup

        service_name = None
        for task_entry in asset_manifest.task_graph:
            if task_entry.task_id == payload.id:
                service_name = task_entry.service
                break

        if not service_name:
            return {
                "status": "error",
                "message": f"Task {payload.id} not found in task graph",
                "task_id": payload.id,
            }

        error_message = None
        if payload.status == "FAILED":
            error_message = payload.get_error_message()

        result_paths = payload.get_all_urls()

        artifacts = []
        if payload.status == "SUCCEEDED" and self.download_artifacts:
            glb_url = payload.get_glb_url()
            if glb_url:
                artifact = self._download_glb_artifact(
                    project=found_project,
                    spec_hash=found_spec_hash,
                    service=service_name,
                    glb_url=glb_url,
                )
                if artifact:
                    artifacts.append(artifact)

        self.repository.record_task_update(
            project=found_project,
            spec_hash=found_spec_hash,
            task_id=payload.id,
            status=payload.status,
            result_paths=result_paths,
            artifacts=artifacts or None,
            source="webhook",
            error=error_message,
        )

        return {
            "status": "success",
            "task_id": payload.id,
            "project": found_project,
            "spec_hash": found_spec_hash,
            "service": service_name,
            "task_status": payload.status,
            "artifacts_downloaded": len(artifacts),
        }

    def _download_glb_artifact(self, project: str, spec_hash: str, service: str, glb_url: str) -> ArtifactRecord | None:
        """Download GLB artifact and create record."""
        try:
            project_dir = self.repository.base_path / project
            filename = f"{spec_hash}_{service}.glb"
            output_path = project_dir / filename

            file_size = base.download(glb_url, str(output_path))

            with open(output_path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()

            return ArtifactRecord(
                relative_path=filename,
                sha256_hash=file_hash,
                file_size_bytes=file_size,
                downloaded_at=_utc_now(),
                source_url=glb_url,
            )

        except Exception:
            return None

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature (stubbed for testing)."""
        return True  # Stub for testing
