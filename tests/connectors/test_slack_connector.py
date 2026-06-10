"""Tests for SlackConnector."""

from __future__ import annotations

import importlib.util

from unittest.mock import MagicMock, patch

import pytest

from extended_data.connectors.slack import SlackConnector
from extended_data.containers import ExtendedDict, ExtendedString


def test_slack_connector_requires_slack_sdk_when_constructed_without_extra():
    """Slack tool metadata imports without slack-sdk, but the connector still requires the extra."""
    if importlib.util.find_spec("slack_sdk") is not None:
        pytest.skip("slack-sdk is installed")

    with pytest.raises(ImportError, match=r"extended-data\[slack\]"):
        SlackConnector(token="xoxp-test", bot_token="xoxb-test", from_environment=False)


class TestSlackConnector:
    """Test suite for SlackConnector."""

    @patch("extended_data.connectors.slack.WebClient")
    def test_init(self, mock_webclient_class, base_connector_kwargs):
        """Test initialization."""
        mock_client = MagicMock()
        mock_webclient_class.return_value = mock_client

        connector = SlackConnector(token="test-token", bot_token="bot-token", **base_connector_kwargs)

        assert connector.web_client is not None
        assert connector.bot_web_client is not None

    @patch("extended_data.connectors.slack.WebClient")
    def test_get_bot_channels(self, mock_webclient_class, base_connector_kwargs):
        """Test getting bot channels."""
        mock_bot_client = MagicMock()
        mock_bot_client.users_conversations.return_value = {
            "channels": [{"name": "general", "id": "C12345"}, {"name": "random", "id": "C67890"}]
        }

        mock_user_client = MagicMock()
        mock_webclient_class.side_effect = [mock_user_client, mock_bot_client]

        connector = SlackConnector(token="test-token", bot_token="bot-token", **base_connector_kwargs)

        channels = connector.get_bot_channels()
        assert isinstance(channels, ExtendedDict)
        assert isinstance(channels["general"], ExtendedDict)
        assert isinstance(channels["general"]["id"], ExtendedString)
        assert "general" in channels
        assert channels["general"]["id"] == "C12345"

    @patch("extended_data.connectors.slack.WebClient")
    def test_send_message(self, mock_webclient_class, base_connector_kwargs):
        """Test sending a message."""
        mock_bot_client = MagicMock()
        mock_bot_client.users_conversations.return_value = {"channels": [{"name": "general", "id": "C12345"}]}
        mock_bot_client.chat_postMessage.return_value = {"ts": "1234567890.123456"}

        mock_user_client = MagicMock()
        mock_webclient_class.side_effect = [mock_user_client, mock_bot_client]

        connector = SlackConnector(token="test-token", bot_token="bot-token", **base_connector_kwargs)

        ts = connector.send_message(channel_name="general", text="Test message", blocks=[])

        assert ts == "1234567890.123456"
        mock_bot_client.chat_postMessage.assert_called_once()

    @patch("extended_data.connectors.slack.SlackConnector._call_api")
    @patch("extended_data.connectors.slack.WebClient")
    def test_list_users_filters_deleted(
        self,
        mock_webclient_class,
        mock_call_api,
        base_connector_kwargs,
    ):
        """Ensure list_users filters deleted and bot accounts."""
        mock_call_api.return_value = {
            "U1": {"id": "U1", "deleted": False, "is_bot": False, "is_app_user": False},
            "U2": {"id": "U2", "deleted": True, "is_bot": False, "is_app_user": False},
            "U3": {"id": "U3", "deleted": False, "is_bot": True, "is_app_user": False},
        }

        mock_user_client = MagicMock()
        mock_bot_client = MagicMock()
        mock_webclient_class.side_effect = [mock_user_client, mock_bot_client]

        connector = SlackConnector(token="test-token", bot_token="bot-token", **base_connector_kwargs)

        users = connector.list_users(
            include_locale=True,
            limit=200,
            team_id="T123",
            include_deleted=False,
            include_bots=False,
            include_app_users=False,
        )

        assert isinstance(users, ExtendedDict)
        assert isinstance(users["U1"], ExtendedDict)
        assert list(users.keys()) == ["U1"]
        mock_call_api.assert_called_once_with(
            "users_list",
            group_by="members",
            include_locale=True,
            limit=200,
            team_id="T123",
        )

    @patch("extended_data.connectors.slack.SlackConnector._call_api")
    @patch("extended_data.connectors.slack.WebClient")
    def test_list_usergroups_filters_ids(
        self,
        mock_webclient_class,
        mock_call_api,
        base_connector_kwargs,
    ):
        """Ensure list_usergroups filters to the requested IDs."""
        mock_call_api.return_value = {
            "S1": {"id": "S1", "name": "Ops"},
            "S2": {"id": "S2", "name": "Eng"},
        }

        mock_user_client = MagicMock()
        mock_bot_client = MagicMock()
        mock_webclient_class.side_effect = [mock_user_client, mock_bot_client]

        connector = SlackConnector(token="test-token", bot_token="bot-token", **base_connector_kwargs)

        groups = connector.list_usergroups(
            include_disabled=True,
            include_count=True,
            include_users=True,
            team_id="T123",
            usergroup_ids="S1,S3",
        )

        assert isinstance(groups, ExtendedDict)
        assert isinstance(groups["S1"]["name"], ExtendedString)
        assert groups == {"S1": {"id": "S1", "name": "Ops"}}
        mock_call_api.assert_called_once_with(
            "usergroups_list",
            group_by="usergroups",
            include_disabled=True,
            include_count=True,
            include_users=True,
            team_id="T123",
        )

    @patch("extended_data.connectors.slack.SlackConnector._call_api")
    @patch("extended_data.connectors.slack.WebClient")
    def test_list_conversations_channels_only(
        self,
        mock_webclient_class,
        mock_call_api,
        base_connector_kwargs,
    ):
        """Ensure list_conversations can filter to Slack channels."""
        mock_call_api.return_value = {
            "C1": {"id": "C1", "is_channel": True},
            "G1": {"id": "G1", "is_channel": False},
        }

        mock_user_client = MagicMock()
        mock_bot_client = MagicMock()
        mock_webclient_class.side_effect = [mock_user_client, mock_bot_client]

        connector = SlackConnector(token="test-token", bot_token="bot-token", **base_connector_kwargs)

        conversations = connector.list_conversations(
            exclude_archived=True,
            limit=50,
            team_id="T123",
            types=["public_channel", "private_channel"],
            channels_only=True,
            cursor="cursor123",
        )

        assert isinstance(conversations, ExtendedDict)
        assert isinstance(conversations["C1"], ExtendedDict)
        assert conversations == {"C1": {"id": "C1", "is_channel": True}}
        mock_call_api.assert_called_once_with(
            "conversations_list",
            group_by="channels",
            exclude_archived=True,
            limit=50,
            team_id="T123",
            types="private_channel,public_channel",
            cursor="cursor123",
        )
