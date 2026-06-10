# ruff: noqa: I001
"""Tests for Google Workspace (Admin Directory) operations."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("google.oauth2.service_account")
pytest.importorskip("googleapiclient")

from extended_data.containers import ExtendedDict, ExtendedList, ExtendedString, extend_data
from extended_data.connectors.google import GoogleConnector


@pytest.fixture
def google_connector():
    """Create Google connector with mocked services."""
    service_account = {
        "type": "service_account",
        "client_email": "test@example.iam.gserviceaccount.com",
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIE...test\n-----END RSA PRIVATE KEY-----\n",
        "private_key_id": "key123",
        "project_id": "test-project",
    }
    with patch("googleapiclient.discovery.build"):
        connector = GoogleConnector(service_account_info=service_account)
        connector.logger = MagicMock()
        return connector


class TestWorkspaceUsers:
    """Tests for Workspace user operations."""

    def test_list_users(self, google_connector):
        """Test listing Workspace users."""
        mock_service = MagicMock()
        mock_users = mock_service.users.return_value
        mock_users.list.return_value.execute.return_value = {
            "users": [
                {"primaryEmail": "user1@example.com", "name": {"fullName": "User One"}},
                {"primaryEmail": "user2@example.com", "name": {"fullName": "User Two"}},
            ]
        }
        google_connector.get_admin_directory_service = MagicMock(return_value=mock_service)

        result = google_connector.list_users()

        assert isinstance(result, ExtendedList)
        assert isinstance(result[0], ExtendedDict)
        assert isinstance(result[0]["primaryEmail"], ExtendedString)
        assert len(result) == 2
        assert result[0]["primaryEmail"] == "user1@example.com"

    def test_list_users_with_domain(self, google_connector):
        """Test listing users filtered by domain."""
        mock_service = MagicMock()
        mock_users = mock_service.users.return_value
        mock_users.list.return_value.execute.return_value = {"users": [{"primaryEmail": "user1@example.com"}]}
        google_connector.get_admin_directory_service = MagicMock(return_value=mock_service)

        result = google_connector.list_users(domain="example.com")

        assert isinstance(result, ExtendedList)
        assert isinstance(result[0], ExtendedDict)
        assert len(result) == 1
        call_args = mock_users.list.call_args[1]
        assert call_args["domain"] == "example.com"

    def test_list_users_pagination(self, google_connector):
        """Test listing users with pagination."""
        mock_service = MagicMock()
        mock_users = mock_service.users.return_value
        mock_users.list.return_value.execute.side_effect = [
            {
                "users": [{"primaryEmail": "user1@example.com"}],
                "nextPageToken": "token123",
            },
            {
                "users": [{"primaryEmail": "user2@example.com"}],
            },
        ]
        google_connector.get_admin_directory_service = MagicMock(return_value=mock_service)

        result = google_connector.list_users()

        assert isinstance(result, ExtendedList)
        assert isinstance(result[0], ExtendedDict)
        assert len(result) == 2
        assert mock_users.list.return_value.execute.call_count == 2

    def test_get_user(self, google_connector):
        """Test getting a specific user."""
        mock_service = MagicMock()
        mock_users = mock_service.users.return_value
        mock_users.get.return_value.execute.return_value = {
            "primaryEmail": "user1@example.com",
            "name": {"fullName": "User One"},
            "suspended": False,
        }
        google_connector.get_admin_directory_service = MagicMock(return_value=mock_service)

        result = google_connector.get_user("user1@example.com")

        assert isinstance(result, ExtendedDict)
        assert isinstance(result["primaryEmail"], ExtendedString)
        assert result["primaryEmail"] == "user1@example.com"
        assert result["suspended"] is False

    def test_get_user_not_found(self, google_connector):
        """Test getting non-existent user."""
        from googleapiclient.errors import HttpError

        mock_service = MagicMock()
        mock_users = mock_service.users.return_value
        mock_resp = MagicMock()
        mock_resp.status = 404
        error = HttpError(mock_resp, b"Not found")
        mock_users.get.return_value.execute.side_effect = error
        google_connector.get_admin_directory_service = MagicMock(return_value=mock_service)

        result = google_connector.get_user("missing@example.com")

        assert result is None

    def test_create_user(self, google_connector):
        """Test creating a new user."""
        mock_service = MagicMock()
        mock_users = mock_service.users.return_value
        mock_users.insert.return_value.execute.return_value = {
            "primaryEmail": "newuser@example.com",
            "name": {"givenName": "New", "familyName": "User"},
        }
        google_connector.get_admin_directory_service = MagicMock(return_value=mock_service)

        result = google_connector.create_user(
            primary_email="newuser@example.com",
            given_name="New",
            family_name="User",
            password="SecurePass123!",
            customSchemas=extend_data({"HR": {"level": "5"}}),
        )

        assert isinstance(result, ExtendedDict)
        assert isinstance(result["primaryEmail"], ExtendedString)
        assert result["primaryEmail"] == "newuser@example.com"
        mock_users.insert.assert_called_once()
        body = mock_users.insert.call_args.kwargs["body"]
        assert isinstance(body, dict)
        assert isinstance(body["customSchemas"], dict)

    def test_update_user(self, google_connector):
        """Test updating a user."""
        mock_service = MagicMock()
        mock_users = mock_service.users.return_value
        mock_users.update.return_value.execute.return_value = {
            "primaryEmail": "user1@example.com",
            "suspended": True,
        }
        google_connector.get_admin_directory_service = MagicMock(return_value=mock_service)

        result = google_connector.update_user(
            "user1@example.com",
            suspended=True,
            customSchemas=extend_data({"HR": {"level": "7"}}),
        )

        assert isinstance(result, ExtendedDict)
        assert result["suspended"] is True
        body = mock_users.update.call_args.kwargs["body"]
        assert isinstance(body, dict)
        assert isinstance(body["customSchemas"], dict)

    def test_delete_user(self, google_connector):
        """Test deleting a user."""
        mock_service = MagicMock()
        mock_users = mock_service.users.return_value
        mock_users.delete.return_value.execute.return_value = {}
        google_connector.get_admin_directory_service = MagicMock(return_value=mock_service)

        google_connector.delete_user("user1@example.com")

        mock_users.delete.assert_called_once_with(userKey="user1@example.com")


class TestWorkspaceGroups:
    """Tests for Workspace group operations."""

    def test_list_groups(self, google_connector):
        """Test listing Workspace groups."""
        mock_service = MagicMock()
        mock_groups = mock_service.groups.return_value
        mock_groups.list.return_value.execute.return_value = {
            "groups": [
                {"email": "group1@example.com", "name": "Group One"},
                {"email": "group2@example.com", "name": "Group Two"},
            ]
        }
        google_connector.get_admin_directory_service = MagicMock(return_value=mock_service)

        result = google_connector.list_groups()

        assert isinstance(result, ExtendedList)
        assert isinstance(result[0], ExtendedDict)
        assert isinstance(result[0]["email"], ExtendedString)
        assert len(result) == 2
        assert result[0]["email"] == "group1@example.com"

    def test_list_groups_with_domain(self, google_connector):
        """Test listing groups filtered by domain."""
        mock_service = MagicMock()
        mock_groups = mock_service.groups.return_value
        mock_groups.list.return_value.execute.return_value = {"groups": [{"email": "group1@example.com"}]}
        google_connector.get_admin_directory_service = MagicMock(return_value=mock_service)

        result = google_connector.list_groups(domain="example.com")

        assert isinstance(result, ExtendedList)
        assert isinstance(result[0], ExtendedDict)
        assert len(result) == 1
        call_args = mock_groups.list.call_args[1]
        assert call_args["domain"] == "example.com"

    def test_get_group(self, google_connector):
        """Test getting a specific group."""
        mock_service = MagicMock()
        mock_groups = mock_service.groups.return_value
        mock_groups.get.return_value.execute.return_value = {
            "email": "group1@example.com",
            "name": "Group One",
            "directMembersCount": "5",
        }
        google_connector.get_admin_directory_service = MagicMock(return_value=mock_service)

        result = google_connector.get_group("group1@example.com")

        assert isinstance(result, ExtendedDict)
        assert isinstance(result["email"], ExtendedString)
        assert result["email"] == "group1@example.com"
        assert result["directMembersCount"] == "5"

    def test_get_group_not_found(self, google_connector):
        """Test getting non-existent group."""
        from googleapiclient.errors import HttpError

        mock_service = MagicMock()
        mock_groups = mock_service.groups.return_value
        mock_resp = MagicMock()
        mock_resp.status = 404
        error = HttpError(mock_resp, b"Not found")
        mock_groups.get.return_value.execute.side_effect = error
        google_connector.get_admin_directory_service = MagicMock(return_value=mock_service)

        result = google_connector.get_group("missing@example.com")

        assert result is None

    def test_create_group(self, google_connector):
        """Test creating a new group."""
        mock_service = MagicMock()
        mock_groups = mock_service.groups.return_value
        mock_groups.insert.return_value.execute.return_value = {
            "email": "newgroup@example.com",
            "name": "New Group",
        }
        google_connector.get_admin_directory_service = MagicMock(return_value=mock_service)

        result = google_connector.create_group(
            email="newgroup@example.com",
            name="New Group",
        )

        assert isinstance(result, ExtendedDict)
        assert isinstance(result["email"], ExtendedString)
        assert result["email"] == "newgroup@example.com"

    def test_list_group_members(self, google_connector):
        """Test listing group members."""
        mock_service = MagicMock()
        mock_members = mock_service.members.return_value
        mock_members.list.return_value.execute.return_value = {
            "members": [
                {"email": "user1@example.com", "role": "MEMBER"},
                {"email": "user2@example.com", "role": "OWNER"},
            ]
        }
        google_connector.get_admin_directory_service = MagicMock(return_value=mock_service)

        result = google_connector.list_group_members("group1@example.com")

        assert isinstance(result, ExtendedList)
        assert isinstance(result[0], ExtendedDict)
        assert isinstance(result[1]["role"], ExtendedString)
        assert len(result) == 2
        assert result[1]["role"] == "OWNER"

    def test_add_group_member(self, google_connector):
        """Test adding a member to a group."""
        mock_service = MagicMock()
        mock_members = mock_service.members.return_value
        mock_members.insert.return_value.execute.return_value = {
            "email": "user1@example.com",
            "role": "MEMBER",
        }
        google_connector.get_admin_directory_service = MagicMock(return_value=mock_service)

        result = google_connector.add_group_member("group1@example.com", "user1@example.com")

        assert isinstance(result, ExtendedDict)
        assert isinstance(result["email"], ExtendedString)
        assert result["email"] == "user1@example.com"

    def test_remove_group_member(self, google_connector):
        """Test removing a member from a group."""
        mock_service = MagicMock()
        mock_members = mock_service.members.return_value
        mock_members.delete.return_value.execute.return_value = {}
        google_connector.get_admin_directory_service = MagicMock(return_value=mock_service)

        google_connector.remove_group_member("group1@example.com", "user1@example.com")

        mock_members.delete.assert_called_once()


class TestWorkspaceOrgUnits:
    """Tests for Workspace organizational unit operations."""

    def test_list_org_units(self, google_connector):
        """Test listing organizational units."""
        mock_service = MagicMock()
        mock_orgunits = mock_service.orgunits.return_value
        mock_orgunits.list.return_value.execute.return_value = {
            "organizationUnits": [
                {"name": "Engineering", "orgUnitPath": "/Engineering"},
                {"name": "Sales", "orgUnitPath": "/Sales"},
            ]
        }
        google_connector.get_admin_directory_service = MagicMock(return_value=mock_service)

        result = google_connector.list_org_units()

        assert isinstance(result, ExtendedList)
        assert isinstance(result[0], ExtendedDict)
        assert isinstance(result[0]["name"], ExtendedString)
        assert len(result) == 2
        assert result[0]["name"] == "Engineering"
