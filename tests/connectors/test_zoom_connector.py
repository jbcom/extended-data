"""Tests for ZoomConnector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from extended_data.connectors.zoom import ZoomConnector
from extended_data.containers import ExtendedDict, ExtendedList, ExtendedString


class TestZoomConnector:
    """Test suite for ZoomConnector."""

    def test_init(self, base_connector_kwargs):
        """Test initialization."""
        connector = ZoomConnector(
            client_id="test-client-id",
            client_secret="test-client-secret",
            account_id="test-account-id",
            **base_connector_kwargs,
        )

        assert connector.client_id == "test-client-id"
        assert connector.client_secret == "test-client-secret"
        assert connector.account_id == "test-account-id"

    @patch("extended_data.connectors.zoom.requests.post")
    def test_get_access_token_success(self, mock_post, base_connector_kwargs):
        """Test successful access token retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "test-access-token"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        connector = ZoomConnector(
            client_id="test-client-id",
            client_secret="test-client-secret",
            account_id="test-account-id",
            **base_connector_kwargs,
        )

        token = connector.get_access_token()
        assert token == "test-access-token"
        mock_post.assert_called_once()

    @patch("extended_data.connectors.zoom.requests.post")
    def test_get_access_token_failure(self, mock_post, base_connector_kwargs):
        """Test failed access token retrieval."""
        import requests

        mock_post.side_effect = requests.exceptions.RequestException("Connection error")

        connector = ZoomConnector(
            client_id="test-client-id",
            client_secret="test-client-secret",
            account_id="test-account-id",
            **base_connector_kwargs,
        )

        with pytest.raises(RuntimeError, match="Failed to get Zoom access token"):
            connector.get_access_token()

    @patch("extended_data.connectors.zoom.requests.get")
    @patch("extended_data.connectors.zoom.requests.post")
    def test_get_zoom_users(self, mock_post, mock_get, base_connector_kwargs):
        """Test getting Zoom users."""
        mock_token_response = MagicMock()
        mock_token_response.json.return_value = {"access_token": "test-token"}
        mock_token_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_token_response

        mock_users_response = MagicMock()
        mock_users_response.json.return_value = {
            "users": [
                {"email": "user1@example.com", "id": "123", "first_name": "User", "last_name": "One"},
                {"email": "user2@example.com", "id": "456", "first_name": "User", "last_name": "Two"},
            ],
            "next_page_token": None,
        }
        mock_users_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_users_response

        connector = ZoomConnector(
            client_id="test-client-id",
            client_secret="test-client-secret",
            account_id="test-account-id",
            **base_connector_kwargs,
        )

        users = connector.get_zoom_users()
        assert isinstance(users, ExtendedDict)
        assert isinstance(users["user1@example.com"], ExtendedDict)
        assert isinstance(users["user1@example.com"]["first_name"], ExtendedString)
        assert "user1@example.com" in users
        assert "user2@example.com" in users
        assert len(users) == 2

    @patch("extended_data.connectors.zoom.requests.post")
    def test_create_zoom_user(self, mock_post, base_connector_kwargs):
        """Test creating a Zoom user."""
        mock_token_response = MagicMock()
        mock_token_response.json.return_value = {"access_token": "test-token"}
        mock_token_response.raise_for_status = MagicMock()

        mock_create_response = MagicMock()
        mock_create_response.raise_for_status = MagicMock()

        mock_post.side_effect = [mock_token_response, mock_create_response]

        connector = ZoomConnector(
            client_id="test-client-id",
            client_secret="test-client-secret",
            account_id="test-account-id",
            **base_connector_kwargs,
        )

        result = connector.create_zoom_user("newuser@example.com", "New", "User")
        assert result is True
        assert mock_post.call_count == 2

    @patch("extended_data.connectors.zoom.requests.get")
    @patch("extended_data.connectors.zoom.requests.post")
    def test_list_users(self, mock_post, mock_get, base_connector_kwargs):
        """Test list_users method (alias for get_zoom_users)."""
        mock_token_response = MagicMock()
        mock_token_response.json.return_value = {"access_token": "test-token"}
        mock_token_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_token_response

        mock_users_response = MagicMock()
        mock_users_response.json.return_value = {
            "users": [
                {"email": "user1@example.com", "id": "123"},
            ],
            "next_page_token": None,
        }
        mock_users_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_users_response

        connector = ZoomConnector(
            client_id="test-client-id",
            client_secret="test-client-secret",
            account_id="test-account-id",
            **base_connector_kwargs,
        )

        users = connector.list_users()
        assert isinstance(users, ExtendedDict)
        assert isinstance(users["user1@example.com"], ExtendedDict)
        assert "user1@example.com" in users

    @patch("extended_data.connectors.zoom.requests.get")
    @patch("extended_data.connectors.zoom.requests.post")
    def test_get_user(self, mock_post, mock_get, base_connector_kwargs):
        """Test getting a specific user."""
        mock_token_response = MagicMock()
        mock_token_response.json.return_value = {"access_token": "test-token"}
        mock_token_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_token_response

        mock_user_response = MagicMock()
        mock_user_response.json.return_value = {
            "id": "123",
            "email": "user1@example.com",
            "first_name": "User",
            "last_name": "One",
        }
        mock_user_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_user_response

        connector = ZoomConnector(
            client_id="test-client-id",
            client_secret="test-client-secret",
            account_id="test-account-id",
            **base_connector_kwargs,
        )

        user = connector.get_user("user1@example.com")
        assert isinstance(user, ExtendedDict)
        assert isinstance(user["first_name"], ExtendedString)
        assert user["email"] == "user1@example.com"
        assert user["id"] == "123"

    @patch("extended_data.connectors.zoom.requests.get")
    @patch("extended_data.connectors.zoom.requests.post")
    def test_list_meetings(self, mock_post, mock_get, base_connector_kwargs):
        """Test listing meetings for a user."""
        mock_token_response = MagicMock()
        mock_token_response.json.return_value = {"access_token": "test-token"}
        mock_token_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_token_response

        mock_meetings_response = MagicMock()
        mock_meetings_response.json.return_value = {
            "meetings": [
                {"id": "111", "topic": "Team Meeting"},
                {"id": "222", "topic": "Client Call"},
            ]
        }
        mock_meetings_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_meetings_response

        connector = ZoomConnector(
            client_id="test-client-id",
            client_secret="test-client-secret",
            account_id="test-account-id",
            **base_connector_kwargs,
        )

        meetings = connector.list_meetings("user1@example.com")
        assert isinstance(meetings, ExtendedList)
        assert isinstance(meetings[0], ExtendedDict)
        assert len(meetings) == 2
        assert meetings[0]["id"] == "111"

    @patch("extended_data.connectors.zoom.requests.get")
    @patch("extended_data.connectors.zoom.requests.post")
    def test_get_meeting(self, mock_post, mock_get, base_connector_kwargs):
        """Test getting a specific meeting."""
        mock_token_response = MagicMock()
        mock_token_response.json.return_value = {"access_token": "test-token"}
        mock_token_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_token_response

        mock_meeting_response = MagicMock()
        mock_meeting_response.json.return_value = {
            "id": "111",
            "topic": "Team Meeting",
            "start_time": "2024-01-15T10:00:00Z",
        }
        mock_meeting_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_meeting_response

        connector = ZoomConnector(
            client_id="test-client-id",
            client_secret="test-client-secret",
            account_id="test-account-id",
            **base_connector_kwargs,
        )

        meeting = connector.get_meeting("111")
        assert isinstance(meeting, ExtendedDict)
        assert isinstance(meeting["topic"], ExtendedString)
        assert meeting["id"] == "111"
        assert meeting["topic"] == "Team Meeting"
