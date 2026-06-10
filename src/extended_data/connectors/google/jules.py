"""Google Jules Connector - HTTP client for Google Jules AI Agent API.

Jules is Google's AI coding agent that can analyze code, create PRs,
and automate development tasks.

Usage:
    from extended_data.connectors.google.jules import JulesConnector

    connector = JulesConnector(api_key="...")

    # List available sources (GitHub repos)
    sources = connector.list_sources()

    # Create a session
    session = connector.create_session(
        prompt="Fix the login bug",
        source="sources/github/org/repo",
        automation_mode="AUTO_CREATE_PR"
    )

    # Poll for completion
    status = connector.get_session(session.name)

Reference: https://developers.google.com/jules/api
"""

from __future__ import annotations

from enum import Enum
from typing import Any

import httpx

from pydantic import BaseModel, Field

from extended_data.connectors.base import VendorConnectorBase


__all__ = [
    "JulesConnector",
    "JulesError",
    "PullRequestOutput",
    "Session",
    "SessionState",
    "Source",
    "SourceContext",
]


class SessionState(str, Enum):
    """Jules session states."""

    UNSPECIFIED = "SESSION_STATE_UNSPECIFIED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    AWAITING_PLAN_APPROVAL = "AWAITING_PLAN_APPROVAL"
    AWAITING_USER_RESPONSE = "AWAITING_USER_RESPONSE"
    CANCELLED = "CANCELLED"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING = "PENDING"
    BLOCKED = "BLOCKED"


class AutomationMode(str, Enum):
    """Automation modes for Jules sessions."""

    UNSPECIFIED = "AUTOMATION_MODE_UNSPECIFIED"
    AUTO_CREATE_PR = "AUTO_CREATE_PR"
    MANUAL = "MANUAL"


class Source(BaseModel):
    """A connected source (e.g., GitHub repository)."""

    name: str = Field(..., description="Resource name (e.g., sources/github/org/repo)")
    id: str = Field(..., description="Source ID")
    github_repo: dict[str, Any] | None = Field(None, alias="githubRepo")


class SourceContext(BaseModel):
    """Context for a session's source."""

    source: str = Field(..., description="Source resource name")
    github_repo_context: dict[str, Any] | None = Field(None, alias="githubRepoContext")


class PullRequestOutput(BaseModel):
    """Pull request created by Jules."""

    url: str = Field(..., description="GitHub PR URL")
    title: str = Field("", description="PR title")
    description: str = Field("", description="PR description")


class Session(BaseModel):
    """A Jules session."""

    model_config = {"extra": "allow"}  # Allow unknown fields

    name: str = Field(..., description="Resource name (e.g., sessions/123)")
    id: str = Field("", description="Session ID")
    title: str = Field("", description="Session title")
    prompt: str = Field("", description="Original prompt")
    state: str | None = Field(None, description="Current state")
    source_context: SourceContext | None = Field(None, alias="sourceContext")
    outputs: list[dict[str, Any]] = Field(default_factory=list, description="Session outputs")

    @property
    def pull_request(self) -> PullRequestOutput | None:
        """Get the pull request output if available."""
        for output in self.outputs:
            if "pullRequest" in output:
                return PullRequestOutput(**output["pullRequest"])
        return None


class JulesError(Exception):
    """Error from Jules API."""

    def __init__(self, message: str, code: int = 0, details: Any = None):
        super().__init__(message)
        self.code = code
        self.details = details


class JulesConnector(VendorConnectorBase):
    """Connector for Google Jules AI Agent API.

    Provides methods to interact with Jules for automated coding tasks.
    """

    BASE_URL = "https://jules.googleapis.com/v1alpha"
    API_KEY_ENV = "JULES_API_KEY"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
        **kwargs: Any,
    ) -> None:
        """Initialize the Jules connector.

        Args:
            api_key: Jules API key. Defaults to JULES_API_KEY env var.
            base_url: API base URL. Defaults to production.
            timeout: Request timeout in seconds.
            **kwargs: Extra arguments for base class.
        """
        super().__init__(api_key=api_key, base_url=base_url, timeout=timeout, **kwargs)

    def _build_headers(self) -> dict[str, str]:
        """Build Jules-specific headers."""
        return {
            "X-Goog-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response, raising on errors."""
        if not response.is_success:
            try:
                error = response.json().get("error", {})
                raise JulesError(
                    error.get("message", response.text),
                    error.get("code", response.status_code),
                    error.get("details"),
                )
            except (ValueError, KeyError) as exc:
                raise JulesError(response.text, response.status_code) from exc
        return response.json()

    # =========================================================================
    # Sources
    # =========================================================================

    def list_sources(self, page_size: int = 100, page_token: str = "") -> list[Source]:
        """List available sources (connected GitHub repos).

        Args:
            page_size: Maximum number of results.
            page_token: Pagination token.

        Returns:
            List of Source objects.
        """
        params: dict[str, Any] = {"pageSize": page_size}
        if page_token:
            params["pageToken"] = page_token

        response = self.get("/sources", params=params)
        data = self._handle_response(response)

        return [Source(**s) for s in data.get("sources", [])]

    # =========================================================================
    # Sessions
    # =========================================================================

    def create_session(
        self,
        prompt: str,
        source: str,
        title: str = "",
        starting_branch: str = "main",
        automation_mode: str = "AUTO_CREATE_PR",
        require_plan_approval: bool = False,
    ) -> Session:
        """Create a new Jules session.

        Args:
            prompt: Task description for Jules.
            source: Source resource name (e.g., sources/github/org/repo).
            title: Optional session title.
            starting_branch: Git branch to start from.
            automation_mode: AUTO_CREATE_PR or MANUAL.
            require_plan_approval: Whether to require explicit plan approval.

        Returns:
            Created Session object.
        """
        body: dict[str, Any] = {
            "prompt": prompt,
            "sourceContext": {
                "source": source,
                "githubRepoContext": {
                    "startingBranch": starting_branch,
                },
            },
            "automationMode": automation_mode,
        }

        if title:
            body["title"] = title
        if require_plan_approval:
            body["requirePlanApproval"] = True

        response = self.post("/sessions", json=body)
        data = self._handle_response(response)

        return Session(**data)

    def get_session(self, session_name: str) -> Session:
        """Get a session by name.

        Args:
            session_name: Full resource name (e.g., sessions/123).

        Returns:
            Session object with current state.
        """
        # Handle both full name and just ID
        if not session_name.startswith("sessions/"):
            session_name = f"sessions/{session_name}"

        response = self.get(f"/{session_name}")
        data = self._handle_response(response)

        return Session(**data)

    def list_sessions(self, page_size: int = 20, page_token: str = "") -> list[Session]:
        """List sessions.

        Args:
            page_size: Maximum number of results.
            page_token: Pagination token.

        Returns:
            List of Session objects.
        """
        params: dict[str, Any] = {"pageSize": page_size}
        if page_token:
            params["pageToken"] = page_token

        response = self.get("/sessions", params=params)
        data = self._handle_response(response)

        return [Session(**s) for s in data.get("sessions", [])]

    def approve_plan(self, session_name: str) -> Session:
        """Approve the plan for a session that requires approval.

        Args:
            session_name: Full resource name.

        Returns:
            Updated Session object.
        """
        if not session_name.startswith("sessions/"):
            session_name = f"sessions/{session_name}"

        response = self.post(f"/{session_name}:approvePlan")
        self._handle_response(response)

        # API returns empty on success, fetch updated session
        return self.get_session(session_name)

    def add_user_response(self, session_name: str, message: str = "") -> Session:
        """Add a follow-up message to a session or resume it.

        Note: The Jules API uses :sendMessage endpoint. An empty body
        resumes a paused session. A message can be included in certain states.

        Args:
            session_name: Full resource name.
            message: Optional user message.

        Returns:
            Updated Session object.
        """
        if not session_name.startswith("sessions/"):
            session_name = f"sessions/{session_name}"

        # The API uses sendMessage, not addUserResponse
        response = self.post(f"/{session_name}:sendMessage", json={})
        self._handle_response(response)

        # API returns empty on success, fetch updated session
        return self.get_session(session_name)

    def resume_session(self, session_name: str) -> Session:
        """Resume a paused or awaiting session.

        Args:
            session_name: Full resource name.

        Returns:
            Updated Session object.
        """
        return self.add_user_response(session_name)
