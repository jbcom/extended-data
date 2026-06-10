"""Extended Data Connectors - shared connectors for cloud, SaaS, and AI platforms.

This package provides modular connectors for various cloud providers and services:
- Anthropic: Claude AI API and Agent SDK (NEW)
- AWS: Organizations, SSO/Identity Center, S3, Secrets Manager
- Cursor: Background Agent API for AI coding agents (NEW)
- Google Cloud: Workspace, Cloud Platform, Billing, Services (GKE, Compute, etc.)
- GitHub: Repository operations, PR management
- Meshy: 3D asset generation
- Slack: Channel and message operations
- Vault: HashiCorp Vault secret management
- Zoom: User and meeting management

Usage:
    # Basic connector (session management + secrets)
    from extended_data.connectors import AWSConnector
    connector = AWSConnector()

    # Full connector with all operations
    from extended_data.connectors.aws import AWSConnectorFull
    connector = AWSConnectorFull()
    accounts = connector.get_accounts()

    # Cursor AI agents
    from extended_data.connectors.cursor import CursorConnector
    cursor = CursorConnector()
    agents = cursor.list_agents()

    # Anthropic Claude AI
    from extended_data.connectors.anthropic import AnthropicConnector
    anthropic = AnthropicConnector()
    response = anthropic.create_message(...)

    # Mixin approach for custom connectors
    from extended_data.connectors.aws import AWSConnector, AWSOrganizationsMixin

    class MyConnector(AWSConnector, AWSOrganizationsMixin):
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
    AWSConnectorFull,
    AWSOrganizationsMixin,
    AWSS3Mixin,
    AWSSSOmixin,
)
from extended_data.connectors.base import VendorConnectorBase
from extended_data.connectors.cloud_params import (
    get_aws_call_params,
    get_cloud_call_params,
    get_google_call_params,
)
from extended_data.connectors.connectors import ConnectorFabric

# Built-in connector classes; vendor SDKs are loaded by connector instances.
from extended_data.connectors.cursor import CursorConnector
from extended_data.connectors.github import GitHubConnector
from extended_data.connectors.google import (
    GoogleBillingConnector,
    GoogleBillingMixin,
    GoogleCloudConnector,
    GoogleCloudMixin,
    GoogleConnector,
    GoogleConnectorFull,
    GoogleServicesMixin,
    GoogleWorkspaceConnector,
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
    "AWSConnectorFull",
    "AWSOrganizationsMixin",
    "AWSS3Mixin",
    "AWSSSOmixin",
    "AnthropicConnector",
    "ConnectorFabric",
    "ConnectorInfo",
    "CursorConnector",
    "GitHubConnector",
    "GoogleBillingConnector",
    "GoogleBillingMixin",
    "GoogleCloudConnector",
    "GoogleCloudMixin",
    "GoogleConnector",
    "GoogleConnectorFull",
    "GoogleServicesMixin",
    "GoogleWorkspaceConnector",
    "GoogleWorkspaceMixin",
    "JulesConnector",
    "MeshyConnector",
    "SecretsConnector",
    "SlackConnector",
    "VaultConnector",
    "VendorConnectorBase",
    "ZoomConnector",
    "__version__",
    "get_aws_call_params",
    "get_cloud_call_params",
    "get_connector",
    "get_connector_class",
    "get_connector_info",
    "get_google_call_params",
    "list_connector_info",
    "list_connectors",
    "meshy",
]

# Registry - unified access to all connectors
from extended_data.connectors.registry import (
    ConnectorInfo,
    get_connector,
    get_connector_class,
    get_connector_info,
    list_connector_info,
    list_connectors,
)
