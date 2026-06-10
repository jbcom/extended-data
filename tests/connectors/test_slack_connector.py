"""Tests for SlackConnector."""

from __future__ import annotations

import importlib.util

from unittest.mock import MagicMock, patch

import pytest

import extended_data.connectors.slack as slack_module

from extended_data.connectors.slack import (
    SlackAPIError,
    SlackConnector,
    get_divider,
    get_field_context_message_blocks,
    get_header_block,
    get_key_value_blocks,
    get_rich_text_blocks,
)
from extended_data.containers import ExtendedDict, ExtendedList, ExtendedString


def test_slack_connector_requires_slack_sdk_when_constructed_without_extra():
    """Slack tool metadata imports without slack-sdk, but the connector still requires the extra."""
    if importlib.util.find_spec("slack_sdk") is not None:
        pytest.skip("slack-sdk is installed")

    with pytest.raises(ImportError, match=r"extended-data\[slack\]"):
        SlackConnector(token="xoxp-test", bot_token="xoxb-test", from_environment=False)


def test_slack_block_helpers_return_extended_payloads():
    """Slack block helper payloads are first-class extended containers."""
    divider = get_divider()
    header = get_header_block("Deploys")
    context = get_field_context_message_blocks("deploy", {"service": "api"})
    key_value = get_key_value_blocks("service", {"name": "api"})
    rich = get_rich_text_blocks(["hello"], bold=True)

    assert isinstance(divider, ExtendedDict)
    assert isinstance(divider["type"], ExtendedString)
    assert isinstance(header, ExtendedList)
    assert isinstance(header[0], ExtendedDict)
    assert isinstance(header[0]["text"], ExtendedDict)
    assert isinstance(context, ExtendedList)
    assert isinstance(context[0], ExtendedDict)
    assert isinstance(key_value, ExtendedList)
    assert isinstance(key_value[0]["text"], ExtendedDict)
    assert isinstance(rich, ExtendedList)
    assert isinstance(rich[0]["elements"], ExtendedList)


def test_slack_module_does_not_export_internal_batching_helper() -> None:
    """Compatibility helpers should not become public connector surface."""
    assert not hasattr(slack_module, "batched")


def test_slack_api_error_redacts_sensitive_response_text() -> None:
    """Slack API errors should not expose raw secret-bearing response values."""
    error = SlackAPIError({"ok": False, "password": "hunter2", "authorization": "Bearer raw_token"})

    message = str(error)
    assert "hunter2" not in message
    assert "raw_token" not in message
    assert "[REDACTED]" in message
    assert error.response["password"] == "[REDACTED]"
    assert error.response["authorization"] == "[REDACTED]"


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

        assert isinstance(ts, ExtendedString)
        assert ts == "1234567890.123456"
        mock_bot_client.chat_postMessage.assert_called_once()

    @patch("extended_data.connectors.slack.WebClient")
    def test_send_message_converts_extended_blocks_for_sdk(self, mock_webclient_class, base_connector_kwargs):
        """Slack SDK calls should receive builtin payloads even when helpers are extended."""
        mock_bot_client = MagicMock()
        mock_bot_client.users_conversations.return_value = {"channels": [{"name": "general", "id": "C12345"}]}
        mock_bot_client.chat_postMessage.return_value = {"ts": "1234567890.123456"}

        mock_user_client = MagicMock()
        mock_webclient_class.side_effect = [mock_user_client, mock_bot_client]

        connector = SlackConnector(token="test-token", bot_token="bot-token", **base_connector_kwargs)

        connector.send_message(channel_name="general", text="Test message", lines=["hello"], bold=True)

        kwargs = mock_bot_client.chat_postMessage.call_args.kwargs
        assert isinstance(kwargs["blocks"], list)
        assert not isinstance(kwargs["blocks"], ExtendedList)
        assert isinstance(kwargs["blocks"][0], dict)
        assert not isinstance(kwargs["blocks"][0], ExtendedDict)
        assert isinstance(kwargs["channel"], str)

    @patch("extended_data.connectors.slack.WebClient")
    def test_send_message_non_raising_api_error_returns_extended_payload(
        self,
        mock_webclient_class,
        base_connector_kwargs,
    ):
        """Non-raising Slack send failures should not leak raw SDK response objects."""

        class FakeSlackApiError(Exception):
            def __init__(self, response):
                self.response = response

        mock_bot_client = MagicMock()
        mock_bot_client.users_conversations.return_value = {"channels": [{"name": "general", "id": "C12345"}]}
        mock_bot_client.chat_postMessage.side_effect = FakeSlackApiError(
            {"ok": False, "error": "channel_not_found", "password": "hunter2"}
        )

        mock_user_client = MagicMock()
        mock_webclient_class.side_effect = [mock_user_client, mock_bot_client]

        connector = SlackConnector(token="test-token", bot_token="bot-token", **base_connector_kwargs)

        with patch("extended_data.connectors.slack.SlackApiError", FakeSlackApiError):
            result = connector.send_message(
                channel_name="general",
                text="Test message",
                blocks=[],
                raise_on_api_error=False,
            )

        assert isinstance(result, ExtendedDict)
        assert isinstance(result["error"], ExtendedString)
        assert result["error"] == "channel_not_found"
        assert result["password"] == "[REDACTED]"

    @patch("extended_data.connectors.slack.WebClient")
    def test_send_message_api_error_redacts_response_without_raw_cause(
        self,
        mock_webclient_class,
        base_connector_kwargs,
    ):
        """Raising Slack send failures should not preserve raw SDK exceptions."""

        class FakeSlackApiError(Exception):
            def __init__(self, response):
                self.response = response

        mock_bot_client = MagicMock()
        mock_bot_client.users_conversations.return_value = {"channels": [{"name": "general", "id": "C12345"}]}
        mock_bot_client.chat_postMessage.side_effect = FakeSlackApiError(
            {"ok": False, "error": "channel_not_found", "password": "hunter2", "token": "raw-token"}
        )

        mock_user_client = MagicMock()
        mock_webclient_class.side_effect = [mock_user_client, mock_bot_client]

        connector = SlackConnector(token="test-token", bot_token="bot-token", **base_connector_kwargs)

        with (
            patch("extended_data.connectors.slack.SlackApiError", FakeSlackApiError),
            pytest.raises(SlackAPIError) as exc_info,
        ):
            connector.send_message(channel_name="general", text="Test message", blocks=[])

        diagnostics = str(exc_info.value) + str(exc_info.value.response)
        assert "hunter2" not in diagnostics
        assert "raw-token" not in diagnostics
        assert "[REDACTED]" in diagnostics
        assert exc_info.value.__cause__ is None

    @patch("extended_data.connectors.slack.WebClient")
    def test_send_message_redacts_missing_channel_name(self, mock_webclient_class, base_connector_kwargs):
        """Missing-channel errors should not echo caller-provided channel names."""
        mock_bot_client = MagicMock()
        mock_bot_client.users_conversations.return_value = {"channels": []}

        mock_user_client = MagicMock()
        mock_webclient_class.side_effect = [mock_user_client, mock_bot_client]

        connector = SlackConnector(token="test-token", bot_token="bot-token", **base_connector_kwargs)

        with pytest.raises(RuntimeError) as exc_info:
            connector.send_message(channel_name="private-channel", text="Test message", blocks=[])

        assert "private-channel" not in str(exc_info.value)
        assert "[REDACTED]" in str(exc_info.value)

    @patch("extended_data.connectors.slack.WebClient")
    def test_get_bot_channels_api_error_redacts_response_without_raw_cause(
        self,
        mock_webclient_class,
        base_connector_kwargs,
    ):
        """Bot-channel lookup failures should wrap redacted Slack responses."""

        class FakeSlackApiError(Exception):
            def __init__(self, response):
                self.response = response

        mock_bot_client = MagicMock()
        mock_bot_client.users_conversations.side_effect = FakeSlackApiError(
            {"ok": False, "error": "token_revoked", "authorization": "Bearer raw_token"}
        )

        mock_user_client = MagicMock()
        mock_webclient_class.side_effect = [mock_user_client, mock_bot_client]

        connector = SlackConnector(token="test-token", bot_token="bot-token", **base_connector_kwargs)

        with (
            patch("extended_data.connectors.slack.SlackApiError", FakeSlackApiError),
            pytest.raises(SlackAPIError) as exc_info,
        ):
            connector.get_bot_channels()

        diagnostics = str(exc_info.value) + str(exc_info.value.response)
        assert "raw_token" not in diagnostics
        assert "[REDACTED]" in diagnostics
        assert exc_info.value.__cause__ is None

    @patch("extended_data.connectors.slack.WebClient")
    def test_call_api_redacts_grouping_failure_payload(self, mock_webclient_class, base_connector_kwargs):
        """Slack grouping failures should not dump raw secret-bearing response data."""
        mock_user_client = MagicMock()
        mock_user_client.users_list.return_value = {
            "members": [{"name": "missing-id", "password": "hunter2", "authorization": "Bearer raw_token"}]
        }
        mock_bot_client = MagicMock()
        mock_webclient_class.side_effect = [mock_user_client, mock_bot_client]

        connector = SlackConnector(token="test-token", bot_token="bot-token", **base_connector_kwargs)

        with pytest.raises(RuntimeError) as exc_info:
            connector._call_api("users_list", group_by="members")

        message = str(exc_info.value)
        assert "hunter2" not in message
        assert "raw_token" not in message
        assert "[REDACTED]" in message

    @patch("extended_data.connectors.slack.WebClient")
    def test_call_api_non_rate_error_redacts_response_without_raw_cause(
        self,
        mock_webclient_class,
        base_connector_kwargs,
    ):
        """Slack API failures should not preserve raw SDK exception causes."""

        class FakeSlackApiError(Exception):
            def __init__(self, response):
                self.response = response

        mock_response = {"ok": False, "error": "bad_auth", "authorization": "Bearer raw_token"}
        mock_user_client = MagicMock()
        mock_user_client.users_list.side_effect = FakeSlackApiError(mock_response)
        mock_bot_client = MagicMock()
        mock_webclient_class.side_effect = [mock_user_client, mock_bot_client]

        connector = SlackConnector(token="test-token", bot_token="bot-token", **base_connector_kwargs)

        with (
            patch("extended_data.connectors.slack.SlackApiError", FakeSlackApiError),
            pytest.raises(SlackAPIError) as exc_info,
        ):
            connector._call_api("users_list")

        diagnostics = str(exc_info.value) + str(exc_info.value.response)
        assert "raw_token" not in diagnostics
        assert "[REDACTED]" in diagnostics
        assert exc_info.value.__cause__ is None

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
