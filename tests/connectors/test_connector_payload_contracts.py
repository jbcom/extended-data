"""Contracts for direct connector payload surfaces."""

from __future__ import annotations

import ast

from pathlib import Path
from typing import Any, get_args, get_origin, get_type_hints

import pytest

from extended_data.connectors.anthropic import AnthropicConnector
from extended_data.connectors.aws import AWSConnector
from extended_data.connectors.aws.codedeploy import create_codedeploy_deployment, get_aws_codedeploy_deployments
from extended_data.connectors.aws.organizations import AWSOrganizationsMixin
from extended_data.connectors.aws.s3 import AWSS3Mixin
from extended_data.connectors.aws.sso import AWSSSOmixin
from extended_data.connectors.cursor import CursorConnector
from extended_data.connectors.github import GitHubConnector
from extended_data.connectors.google import GoogleConnector
from extended_data.connectors.google.billing import GoogleBillingMixin
from extended_data.connectors.google.cloud import GoogleCloudMixin
from extended_data.connectors.google.jules import JulesConnector
from extended_data.connectors.google.services import GoogleServicesMixin
from extended_data.connectors.google.workspace import GoogleWorkspaceMixin
from extended_data.connectors.meshy.connector import MeshyConnector
from extended_data.connectors.slack import SlackConnector
from extended_data.connectors.vault import VaultConnector
from extended_data.connectors.zoom import ZoomConnector
from extended_data.containers import ExtendedDict, ExtendedList, ExtendedString


REPO_ROOT = Path(__file__).resolve().parents[2]

PAYLOAD_METHODS = (
    (AnthropicConnector.create_message, ExtendedDict),
    (AnthropicConnector.list_models, ExtendedList[ExtendedDict]),
    (AnthropicConnector.get_model, ExtendedDict),
    (AWSConnector.get_caller_account_id, ExtendedString),
    (AWSConnector.get_secret, ExtendedString | None),
    (AWSConnector.list_secrets, ExtendedDict),
    (AWSConnector.create_secret, ExtendedDict),
    (AWSConnector.update_secret, ExtendedDict),
    (AWSConnector.delete_secret, ExtendedDict),
    (AWSConnector.delete_secrets_matching, ExtendedList[ExtendedString]),
    (AWSConnector.copy_secrets_to_s3, ExtendedString),
    (AWSConnector.load_vendors_from_asm, ExtendedDict),
    (AWSOrganizationsMixin.get_organization_accounts, ExtendedDict),
    (AWSOrganizationsMixin.get_controltower_accounts, ExtendedDict),
    (AWSOrganizationsMixin.get_accounts, ExtendedDict),
    (AWSOrganizationsMixin.get_organization_units, ExtendedDict),
    (AWSOrganizationsMixin.classify_accounts, ExtendedDict),
    (AWSOrganizationsMixin.label_aws_accounts, ExtendedDict),
    (AWSOrganizationsMixin.label_aws_account, ExtendedDict),
    (AWSOrganizationsMixin.classify_aws_accounts, ExtendedDict),
    (AWSOrganizationsMixin.preprocess_aws_organization, ExtendedDict),
    (AWSOrganizationsMixin.preprocess_organization, ExtendedDict),
    (AWSS3Mixin.list_s3_buckets, ExtendedDict),
    (AWSS3Mixin.get_bucket_location, ExtendedString),
    (AWSS3Mixin.get_object, ExtendedString | bytes | None),
    (AWSS3Mixin.get_json_object, ExtendedDict | ExtendedList[Any] | None),
    (AWSS3Mixin.put_object, ExtendedDict),
    (AWSS3Mixin.put_json_object, ExtendedDict),
    (AWSS3Mixin.delete_object, ExtendedDict),
    (AWSS3Mixin.list_objects, ExtendedList[ExtendedDict]),
    (AWSS3Mixin.copy_object, ExtendedDict),
    (AWSS3Mixin.get_bucket_features, ExtendedDict),
    (AWSS3Mixin.find_buckets_by_name, ExtendedDict),
    (AWSS3Mixin.create_bucket, ExtendedDict),
    (AWSS3Mixin.get_bucket_tags, ExtendedDict),
    (AWSS3Mixin.get_bucket_sizes, ExtendedDict),
    (AWSSSOmixin.get_identity_store_id, ExtendedString),
    (AWSSSOmixin.get_sso_instance_arn, ExtendedString),
    (AWSSSOmixin.list_sso_users, ExtendedDict),
    (AWSSSOmixin.get_sso_user, ExtendedDict | None),
    (AWSSSOmixin.create_sso_user, ExtendedDict),
    (AWSSSOmixin.list_sso_groups, ExtendedDict),
    (AWSSSOmixin.create_sso_group, ExtendedDict),
    (AWSSSOmixin.add_user_to_group, ExtendedDict),
    (AWSSSOmixin.list_permission_sets, ExtendedDict),
    (AWSSSOmixin.list_account_assignments, ExtendedList[ExtendedDict]),
    (AWSSSOmixin.create_account_assignment, ExtendedDict),
    (AWSSSOmixin.delete_account_assignment, ExtendedDict),
    (get_aws_codedeploy_deployments, ExtendedDict),
    (create_codedeploy_deployment, ExtendedDict),
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
    (MeshyConnector.text3d_generate, ExtendedDict | ExtendedString),
    (MeshyConnector.image3d_generate, ExtendedDict | ExtendedString),
    (MeshyConnector.rig_model, ExtendedDict | ExtendedString),
    (MeshyConnector.apply_animation, ExtendedDict | ExtendedString),
    (MeshyConnector.retexture_model, ExtendedDict | ExtendedString),
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

RAW_CONNECTOR_BOUNDARIES = {
    ("src/extended_data/connectors/ai_tools.py", "build_langchain_tools"),
    ("src/extended_data/connectors/base.py", "VendorConnectorBase.get_tools"),
    ("src/extended_data/connectors/connectors.py", "ConnectorFabric.list_connectors"),
    ("src/extended_data/connectors/registry.py", "list_connectors"),
    ("src/extended_data/connectors/zoom/__init__.py", "ZoomConnector.get_headers"),
}


class _RawContainerReturnVisitor(ast.NodeVisitor):
    def __init__(self, relative_path: str) -> None:
        self.relative_path = relative_path
        self.class_stack: list[str] = []
        self.function_depth = 0
        self.offenders: list[str] = []

    def visit_If(self, node: ast.If) -> None:
        if ast.unparse(node.test) == "TYPE_CHECKING":
            return
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_stack.append(node.name)
        self.generic_visit(node)
        self.class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        is_nested_function = self.function_depth > 0
        qualname = ".".join([*self.class_stack, node.name])

        if not is_nested_function and not node.name.startswith("_") and node.returns is not None:
            annotation = ast.unparse(node.returns)
            has_raw_container = any(token in annotation for token in ("dict", "list"))
            if has_raw_container and "Extended" not in annotation:
                boundary = (self.relative_path, qualname)
                if boundary not in RAW_CONNECTOR_BOUNDARIES:
                    self.offenders.append(f"{self.relative_path}:{node.lineno}: {qualname} -> {annotation}")

        self.function_depth += 1
        self.generic_visit(node)
        self.function_depth -= 1


@pytest.mark.parametrize(("method", "expected_return"), PAYLOAD_METHODS)
def test_direct_connector_methods_advertise_extended_payloads(method: object, expected_return: object) -> None:
    """Public connector data methods expose Tier 2 payload contracts."""
    return_type = get_type_hints(method)["return"]

    if get_origin(expected_return) is ExtendedList:
        assert get_origin(return_type) is ExtendedList
        assert get_args(return_type) == get_args(expected_return)
        return

    assert return_type == expected_return


def test_raw_connector_container_returns_are_explicit_boundaries() -> None:
    """Public connector payloads should not drift back to plain dict/list returns."""
    offenders: list[str] = []

    for path in sorted((REPO_ROOT / "src/extended_data/connectors").rglob("*.py")):
        if path.name == "tools.py":
            continue

        relative_path = path.relative_to(REPO_ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        visitor = _RawContainerReturnVisitor(relative_path)
        visitor.visit(tree)
        offenders.extend(visitor.offenders)

    assert offenders == []
