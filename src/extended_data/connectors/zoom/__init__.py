"""Zoom connector built on extended-data primitives."""

from __future__ import annotations

import base64

from typing import Any

import requests

from extended_data.connectors.base import VendorConnectorBase
from extended_data.containers import ExtendedDict, ExtendedList
from extended_data.logging import Logging
from extended_data.primitives.redaction import redact_sensitive_text


# Default timeout for HTTP requests in seconds
DEFAULT_REQUEST_TIMEOUT = 30


def _safe_zoom_text(value: Any, *sensitive_values: Any) -> str:
    """Redact secrets and request identifiers from Zoom diagnostics."""
    return redact_sensitive_text(value, values=sensitive_values)


def _zoom_error(action: str, exc: BaseException, *sensitive_values: Any) -> str:
    """Build a redacted Zoom operational error message."""
    return f"{action}: {_safe_zoom_text(exc, *sensitive_values)}"


class ZoomConnector(VendorConnectorBase):
    """Zoom connector for user management."""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        account_id: str | None = None,
        logger: Logging | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(logger=logger, **kwargs)
        self.errors: list[str] = []  # Track errors for programmatic access

        self.client_id = client_id or self.get_input("ZOOM_CLIENT_ID", required=True)
        self.client_secret = client_secret or self.get_input("ZOOM_CLIENT_SECRET", required=True)
        self.account_id = account_id or self.get_input("ZOOM_ACCOUNT_ID", required=True)

    def get_access_token(self) -> str | None:
        """Get an OAuth access token from Zoom."""
        url = "https://zoom.us/oauth/token"
        auth_string = f"{self.client_id}:{self.client_secret}"
        headers = {
            "Authorization": f"Basic {base64.b64encode(auth_string.encode()).decode()}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"grant_type": "account_credentials", "account_id": self.account_id}

        try:
            response = requests.post(url, headers=headers, data=data, timeout=DEFAULT_REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json().get("access_token")
        except requests.exceptions.RequestException as exc:
            msg = "Failed to get Zoom access token"
            raise RuntimeError(msg) from exc

    def get_headers(self) -> dict[str, str]:
        """Get headers with authorization for Zoom API calls."""
        token = self.get_access_token()
        if not token:
            msg = "Failed to get access token"
            raise RuntimeError(msg)
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def list_users(self) -> ExtendedDict:
        """List all Zoom users.

        Returns:
            Dictionary mapping user emails to user data.
        """
        url = "https://api.zoom.us/v2/users"
        headers = self.get_headers()
        users: dict[str, dict[str, Any]] = {}
        page_size = 300
        next_page_token = None

        while True:
            params: dict[str, Any] = {"page_size": page_size}
            if next_page_token:
                params["next_page_token"] = next_page_token

            try:
                response = requests.get(url, headers=headers, params=params, timeout=DEFAULT_REQUEST_TIMEOUT)
                response.raise_for_status()
                data = response.json()
                for user in data.get("users", []):
                    users[user["email"]] = user

                next_page_token = data.get("next_page_token")
                if not next_page_token:
                    break
            except requests.exceptions.RequestException as exc:
                raise RuntimeError(_zoom_error("Failed to get Zoom users", exc)) from exc

        return self.extend_result(users)

    def remove_zoom_user(self, email: str) -> None:
        """Remove a Zoom user."""
        url = f"https://api.zoom.us/v2/users/{email}"
        headers = self.get_headers()
        try:
            response = requests.delete(url, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT)
            response.raise_for_status()
            self.logger.warning("Removed Zoom user")
        except requests.exceptions.RequestException as exc:
            error_msg = _zoom_error("Failed to remove Zoom user", exc, email)
            self.errors.append(error_msg)
            self.logger.exception(error_msg)

    def create_zoom_user(self, email: str, first_name: str, last_name: str) -> bool:
        """Create a Zoom user with a paid license."""
        url = "https://api.zoom.us/v2/users"
        headers = self.get_headers()
        user_info = {
            "action": "create",
            "user_info": {"email": email, "type": 2, "first_name": first_name, "last_name": last_name},
        }
        try:
            response = requests.post(url, headers=headers, json=user_info, timeout=DEFAULT_REQUEST_TIMEOUT)
            response.raise_for_status()
            self.logger.info("Created Zoom user")
            return True
        except requests.exceptions.RequestException as exc:
            error_msg = _zoom_error("Failed to create Zoom user", exc, email, first_name, last_name)
            self.errors.append(error_msg)
            self.logger.exception(error_msg)
            return False

    def get_user(self, user_id: str) -> ExtendedDict:
        """Get a specific Zoom user by ID or email.

        Args:
            user_id: User ID or email address

        Returns:
            User data dictionary
        """
        url = f"https://api.zoom.us/v2/users/{user_id}"
        headers = self.get_headers()

        try:
            response = requests.get(url, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT)
            response.raise_for_status()
            return self.extend_result(response.json())
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(_zoom_error("Failed to get Zoom user", exc, user_id)) from exc

    def list_meetings(self, user_id: str, meeting_type: str = "scheduled") -> ExtendedList[ExtendedDict]:
        """List meetings for a specific user.

        Args:
            user_id: User ID or email address
            meeting_type: Type of meetings to list (scheduled, live, upcoming, previous_meetings)

        Returns:
            List of meeting data dictionaries
        """
        url = f"https://api.zoom.us/v2/users/{user_id}/meetings"
        headers = self.get_headers()
        params = {"type": meeting_type}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=DEFAULT_REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            return self.extend_result(data.get("meetings", []))
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(_zoom_error("Failed to list Zoom meetings", exc, user_id)) from exc

    def get_meeting(self, meeting_id: str) -> ExtendedDict:
        """Get details of a specific meeting.

        Args:
            meeting_id: Meeting ID

        Returns:
            Meeting data dictionary
        """
        url = f"https://api.zoom.us/v2/meetings/{meeting_id}"
        headers = self.get_headers()

        try:
            response = requests.get(url, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT)
            response.raise_for_status()
            return self.extend_result(response.json())
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(_zoom_error("Failed to get Zoom meeting", exc, meeting_id)) from exc


from extended_data.connectors.zoom.tools import (
    get_crewai_tools,
    get_langchain_tools,
    get_strands_tools,
    get_tools,
)


__all__ = [
    # Core connector
    "ZoomConnector",
    "get_crewai_tools",
    "get_langchain_tools",
    "get_strands_tools",
    # Tools
    "get_tools",
]
