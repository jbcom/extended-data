"""Contracts for direct connector payload surfaces."""

from __future__ import annotations

from typing import get_args, get_origin, get_type_hints

import pytest

from extended_data.connectors.anthropic import AnthropicConnector
from extended_data.connectors.cursor import CursorConnector
from extended_data.connectors.github import GitHubConnector
from extended_data.connectors.slack import SlackConnector
from extended_data.connectors.vault import VaultConnector
from extended_data.connectors.zoom import ZoomConnector
from extended_data.containers import ExtendedDict, ExtendedList, ExtendedString


PAYLOAD_METHODS = (
    (AnthropicConnector.create_message, ExtendedDict),
    (AnthropicConnector.list_models, ExtendedList[ExtendedDict]),
    (AnthropicConnector.get_model, ExtendedDict),
    (CursorConnector.list_agents, ExtendedList[ExtendedDict]),
    (CursorConnector.get_agent_status, ExtendedDict),
    (CursorConnector.get_agent_conversation, ExtendedDict),
    (CursorConnector.launch_agent, ExtendedDict),
    (CursorConnector.list_repositories, ExtendedList[ExtendedDict]),
    (CursorConnector.list_models, ExtendedList[ExtendedString]),
    (GitHubConnector.list_org_members, ExtendedDict),
    (GitHubConnector.get_org_member, ExtendedDict | None),
    (GitHubConnector.list_repositories, ExtendedDict),
    (GitHubConnector.get_repository, ExtendedDict | None),
    (GitHubConnector.list_teams, ExtendedDict),
    (GitHubConnector.get_team, ExtendedDict | None),
    (GitHubConnector.execute_graphql, ExtendedDict),
    (GitHubConnector.get_users_with_verified_emails, ExtendedDict),
    (GitHubConnector.build_workflow, ExtendedDict),
    (GitHubConnector.build_workflow_job, ExtendedDict),
    (GitHubConnector.build_workflow_step, ExtendedDict),
    (GitHubConnector.create_python_ci_workflow, ExtendedDict),
    (SlackConnector.get_bot_channels, ExtendedDict),
    (SlackConnector.list_users, ExtendedDict),
    (SlackConnector.list_usergroups, ExtendedDict),
    (SlackConnector.list_conversations, ExtendedDict),
    (VaultConnector.list_secrets, ExtendedDict),
    (VaultConnector.read_secret, ExtendedDict | None),
    (VaultConnector.get_secret, ExtendedDict | None),
    (VaultConnector.list_aws_iam_roles, ExtendedList[ExtendedString]),
    (VaultConnector.get_aws_iam_role, ExtendedDict | None),
    (VaultConnector.generate_aws_credentials, ExtendedDict),
    (ZoomConnector.get_zoom_users, ExtendedDict),
    (ZoomConnector.list_users, ExtendedDict),
    (ZoomConnector.get_user, ExtendedDict),
    (ZoomConnector.list_meetings, ExtendedList[ExtendedDict]),
    (ZoomConnector.get_meeting, ExtendedDict),
)


@pytest.mark.parametrize(("method", "expected_return"), PAYLOAD_METHODS)
def test_direct_connector_methods_advertise_extended_payloads(method: object, expected_return: object) -> None:
    """Public connector data methods expose Tier 2 payload contracts."""
    return_type = get_type_hints(method)["return"]

    if get_origin(expected_return) is ExtendedList:
        assert get_origin(return_type) is ExtendedList
        assert get_args(return_type) == get_args(expected_return)
        return

    assert return_type == expected_return
