"""Contracts for direct connector payload surfaces."""

from __future__ import annotations

from typing import get_args, get_origin, get_type_hints

import pytest

from extended_data.connectors.anthropic import AnthropicConnector
from extended_data.connectors.cursor import CursorConnector
from extended_data.connectors.github import GitHubConnector
from extended_data.connectors.google import GoogleConnector
from extended_data.connectors.google.billing import GoogleBillingMixin
from extended_data.connectors.google.cloud import GoogleCloudMixin
from extended_data.connectors.google.jules import JulesConnector
from extended_data.connectors.google.services import GoogleServicesMixin
from extended_data.connectors.google.workspace import GoogleWorkspaceMixin
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
    (GoogleConnector.list_users, ExtendedList[ExtendedDict] | ExtendedDict),
    (GoogleConnector.list_groups, ExtendedList[ExtendedDict] | ExtendedDict),
    (GoogleBillingMixin.list_billing_accounts, ExtendedList[ExtendedDict]),
    (GoogleBillingMixin.get_billing_account, ExtendedDict | None),
    (GoogleBillingMixin.get_project_billing_info, ExtendedDict | None),
    (GoogleBillingMixin.update_project_billing_info, ExtendedDict),
    (GoogleBillingMixin.disable_project_billing, ExtendedDict),
    (GoogleBillingMixin.list_billing_account_projects, ExtendedList[ExtendedDict]),
    (GoogleBillingMixin.get_billing_account_iam_policy, ExtendedDict),
    (GoogleBillingMixin.set_billing_account_iam_policy, ExtendedDict),
    (GoogleBillingMixin.get_bigquery_billing_dataset, ExtendedDict | None),
    (GoogleBillingMixin.setup_billing_export, ExtendedDict),
    (GoogleCloudMixin.get_organization_id, ExtendedString),
    (GoogleCloudMixin.get_organization, ExtendedDict),
    (GoogleCloudMixin.list_projects, ExtendedList[ExtendedDict]),
    (GoogleCloudMixin.get_project, ExtendedDict | None),
    (GoogleCloudMixin.create_project, ExtendedDict),
    (GoogleCloudMixin.delete_project, ExtendedDict),
    (GoogleCloudMixin.move_project, ExtendedDict),
    (GoogleCloudMixin.list_folders, ExtendedList[ExtendedDict]),
    (GoogleCloudMixin.get_org_policy, ExtendedDict | None),
    (GoogleCloudMixin.set_org_policy, ExtendedDict),
    (GoogleCloudMixin.get_iam_policy, ExtendedDict),
    (GoogleCloudMixin.set_iam_policy, ExtendedDict),
    (GoogleCloudMixin.add_iam_binding, ExtendedDict),
    (GoogleCloudMixin.list_service_accounts, ExtendedList[ExtendedDict]),
    (GoogleCloudMixin.create_service_account, ExtendedDict),
    (GoogleWorkspaceMixin.list_workspace_users, ExtendedList[ExtendedDict]),
    (GoogleWorkspaceMixin.get_user, ExtendedDict | None),
    (GoogleWorkspaceMixin.create_user, ExtendedDict),
    (GoogleWorkspaceMixin.update_user, ExtendedDict),
    (GoogleWorkspaceMixin.list_workspace_groups, ExtendedList[ExtendedDict]),
    (GoogleWorkspaceMixin.get_group, ExtendedDict | None),
    (GoogleWorkspaceMixin.create_group, ExtendedDict),
    (GoogleWorkspaceMixin.list_group_members, ExtendedList[ExtendedDict]),
    (GoogleWorkspaceMixin.add_group_member, ExtendedDict),
    (GoogleWorkspaceMixin.list_org_units, ExtendedList[ExtendedDict]),
    (GoogleWorkspaceMixin.create_or_update_user, ExtendedDict),
    (GoogleWorkspaceMixin.create_or_update_group, ExtendedDict),
    (GoogleWorkspaceMixin.list_available_licenses, ExtendedList[ExtendedDict]),
    (GoogleWorkspaceMixin.get_license_summary, ExtendedDict),
    (GoogleServicesMixin.list_compute_instances, ExtendedList[ExtendedDict]),
    (GoogleServicesMixin.list_gke_clusters, ExtendedList[ExtendedDict]),
    (GoogleServicesMixin.get_gke_cluster, ExtendedDict | None),
    (GoogleServicesMixin.list_storage_buckets, ExtendedList[ExtendedDict]),
    (GoogleServicesMixin.list_sql_instances, ExtendedList[ExtendedDict]),
    (GoogleServicesMixin.list_pubsub_topics, ExtendedList[ExtendedDict]),
    (GoogleServicesMixin.list_pubsub_subscriptions, ExtendedList[ExtendedDict]),
    (GoogleServicesMixin.list_enabled_services, ExtendedList[ExtendedDict]),
    (GoogleServicesMixin.enable_service, ExtendedDict),
    (GoogleServicesMixin.disable_service, ExtendedDict),
    (GoogleServicesMixin.batch_enable_services, ExtendedDict),
    (GoogleServicesMixin.list_kms_keyrings, ExtendedList[ExtendedDict]),
    (GoogleServicesMixin.create_kms_keyring, ExtendedDict),
    (GoogleServicesMixin.create_kms_key, ExtendedDict),
    (GoogleServicesMixin.get_project_iam_users, ExtendedDict),
    (GoogleServicesMixin.get_pubsub_resources_for_project, ExtendedDict),
    (GoogleServicesMixin.find_inactive_projects, ExtendedList[ExtendedDict]),
    (JulesConnector.list_sources, ExtendedList[ExtendedDict]),
    (JulesConnector.create_session, ExtendedDict),
    (JulesConnector.get_session, ExtendedDict),
    (JulesConnector.list_sessions, ExtendedList[ExtendedDict]),
    (JulesConnector.approve_plan, ExtendedDict),
    (JulesConnector.add_user_response, ExtendedDict),
    (JulesConnector.resume_session, ExtendedDict),
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
