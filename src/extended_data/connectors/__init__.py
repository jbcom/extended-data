"""Extended Data Connectors - shared connectors for cloud, SaaS, and AI platforms.

This package provides modular connectors for various cloud providers and services:
- Anthropic: Claude AI API and Agent SDK
- AWS: Organizations, SSO/Identity Center, S3, Secrets Manager
- Cursor: Background Agent API for AI coding agents
- Google Cloud: Workspace, Cloud Platform, Billing, Services (GKE, Compute, etc.)
- GitHub: Repository operations, PR management
- Meshy: 3D asset generation
- Slack: Channel and message operations
- Vault: HashiCorp Vault secret management
- Zoom: User and meeting management

Usage:
    # AWS connector with session management, secrets, Organizations, SSO, and S3
    from extended_data.connectors import AWSConnector
    connector = AWSConnector()
    accounts = connector.get_accounts()

    # Cursor AI agents
    from extended_data.connectors.cursor import CursorConnector
    cursor = CursorConnector()
    agents = cursor.list_agents()

    # Anthropic Claude AI
    from extended_data.connectors.anthropic import AnthropicConnector
    anthropic = AnthropicConnector()
    response = anthropic.create_message(...)

    # Custom connector behavior can subclass the unified connector
    from extended_data.connectors.aws import AWSConnector

    class MyConnector(AWSConnector):
        pass

    # Meshy AI 3D generation (functional interface)
    from extended_data.connectors.meshy import text3d, image3d, rigging, animate

    model = text3d.generate("a medieval sword")
    rigged = rigging.rig(model.id)
    animated = animate.apply(rigged.id, animation_id=0)

    # AI tools and automation integrations
    from extended_data.connectors.meshy.tools import get_tools, get_crewai_tools
    from extended_data.connectors.meshy.mcp import create_server, run_server
"""

from __future__ import annotations

from extended_data._version import __version__

# Core package primitives
from extended_data.connectors import meshy
from extended_data.connectors.anthropic import AnthropicConnector
from extended_data.connectors.aws import (
    AWSConnector,
    AWSOrganizationsMixin,
    AWSS3Mixin,
    AWSSSOmixin,
)
from extended_data.connectors.base import ConnectorBase
from extended_data.connectors.cloud_params import (
    get_aws_call_params,
    get_cloud_call_params,
    get_google_call_params,
)
from extended_data.connectors.connectors import ConnectorFabric

# Built-in connector classes; optional SDKs are loaded by connector instances.
from extended_data.connectors.cursor import CursorConnector
from extended_data.connectors.github import GitHubConnector
from extended_data.connectors.google import (
    GoogleBillingMixin,
    GoogleCloudMixin,
    GoogleConnector,
    GoogleServicesMixin,
    GoogleWorkspaceMixin,
    JulesConnector,
)
from extended_data.connectors.meshy import MeshyConnector
from extended_data.connectors.secrets import SecretsConnector
from extended_data.connectors.slack import SlackConnector
from extended_data.connectors.vault import VaultConnector
from extended_data.connectors.zoom import ZoomConnector


__all__ = [
    "AWSConnector",
    "AWSOrganizationsMixin",
    "AWSS3Mixin",
    "AWSSSOmixin",
    "AnthropicConnector",
    "ConnectorBase",
    "ConnectorFabric",
    "ConnectorInfo",
    "CursorConnector",
    "GitHubConnector",
    "GoogleBillingMixin",
    "GoogleCloudMixin",
    "GoogleConnector",
    "GoogleServicesMixin",
    "GoogleWorkspaceMixin",
    "JulesConnector",
    "MeshyConnector",
    "SecretsConnector",
    "SlackConnector",
    "VaultConnector",
    "ZoomConnector",
    "__version__",
    "get_aws_call_params",
    "get_cloud_call_params",
    "get_connector",
    "get_connector_class",
    "get_connector_info",
    "get_google_call_params",
    "list_available_connectors",
    "list_connector_capabilities",
    "list_connector_categories",
    "list_connector_info",
    "list_connectors",
    "list_connectors_by_capability",
    "list_connectors_by_category",
    "meshy",
]

# Registry - unified access to all connectors
from extended_data.connectors.registry import (
    ConnectorInfo,
    get_connector,
    get_connector_class,
    get_connector_info,
    list_available_connectors,
    list_connector_capabilities,
    list_connector_categories,
    list_connector_info,
    list_connectors,
    list_connectors_by_capability,
    list_connectors_by_category,
)
