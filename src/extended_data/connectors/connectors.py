"""ConnectorFabric - Public API with caching like TerraformDataSource."""

from __future__ import annotations

import hashlib

from typing import TYPE_CHECKING, Any

from extended_data import get_default_dict, get_unique_signature, make_hashable

# Import zoom directly (no extra deps)
from extended_data.connectors.registry import (
    get_connector_class,
)
from extended_data.connectors.registry import (
    get_connector_info as get_registered_connector_info,
)
from extended_data.connectors.registry import (
    list_connector_info as list_registered_connector_info,
)
from extended_data.connectors.registry import (
    list_connectors as list_registered_connectors,
)
from extended_data.connectors.zoom import ZoomConnector
from extended_data.containers import ExtendedDict, ExtendedList
from extended_data.inputs import InputProvider
from extended_data.logging import Logging


# Optional connectors - imported lazily when methods are called
# This allows the package to be imported without all vendor SDKs installed

if TYPE_CHECKING:
    import boto3
    import hvac

    from boto3.resources.base import ServiceResource
    from botocore.config import Config

    from extended_data.connectors.aws import AWSConnector
    from extended_data.connectors.github import GitHubConnector
    from extended_data.connectors.google import GoogleConnector
    from extended_data.connectors.slack import SlackConnector
    from extended_data.connectors.vault import VaultConnector


class ConnectorFabric(InputProvider):
    """Public API for extended data connectors with client caching.

    This class provides cached access to all extended data connectors, similar to
    how TerraformDataSource works in terraform-modules libraries.

    Usage:
        vc = ConnectorFabric()
        slack = vc.get_slack_client(token="...", bot_token="...")
        github = vc.get_github_client(github_owner="org", github_token="...")
        aws_client = vc.get_aws_client("s3")

    For Meshy AI, use the functional interface directly:
        from extended_data.connectors.meshy import text3d, image3d, rigging, animate
        model = text3d.generate("a medieval sword")

    Meshy does not provide a `get_meshy_client()` method because it uses a functional interface
    rather than a connector class, in order to simplify async operations and usage.
    """

    def __init__(
        self,
        logger: Logging | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.logging = logger or Logging(logger_name=get_unique_signature(self))
        self.logger = self.logging.logger

        # Client cache - nested dict for different client types and their params
        self._client_cache: dict[str, dict[frozenset[tuple[str, Any]], Any]] = get_default_dict(levels=2)

    def _get_cache_key(self, **kwargs: Any) -> frozenset[tuple[str, Any]]:
        """Generate a hashable cache key from kwargs."""
        hashable_kwargs = {k: make_hashable(v) for k, v in kwargs.items()}
        return frozenset(hashable_kwargs.items())

    def _get_cached_client(self, client_type: str, **kwargs: Any) -> Any | None:
        """Retrieve a client from cache."""
        cache_key = self._get_cache_key(**kwargs)
        return self._client_cache[client_type].get(cache_key)

    def _set_cached_client(self, client_type: str, client: Any, **kwargs: Any) -> None:
        """Store a client in cache."""
        cache_key = self._get_cache_key(**kwargs)
        self._client_cache[client_type][cache_key] = client

    def list_connectors(self) -> dict[str, Any]:
        """List connector classes available in the current environment."""
        return list_registered_connectors()

    def list_connector_info(self, *, include_unavailable: bool = True) -> ExtendedList[ExtendedDict]:
        """List connector catalog metadata."""
        return list_registered_connector_info(include_unavailable=include_unavailable)

    def get_connector_info(self, name: str, *, include_unavailable: bool = True) -> ExtendedDict:
        """Get catalog metadata for one connector."""
        return get_registered_connector_info(name, include_unavailable=include_unavailable)

    def get_connector(self, name: str, **kwargs: Any) -> Any:
        """Get a cached connector instance by registry name.

        The connector receives the fabric's shared inputs and logger unless
        explicit values are passed in ``kwargs``. This is the generic path for
        vendor adapters that are registered through entry points or built-ins.
        """
        connector_name = name.strip().lower()
        cache_kwargs = {"name": connector_name, **kwargs}

        cached = self._get_cached_client("connector", **cache_kwargs)
        if cached:
            return cached

        connector_cls = get_connector_class(connector_name)
        connector_kwargs = dict(kwargs)
        connector_kwargs.setdefault("logger", self.logging)
        connector_kwargs.setdefault("inputs", self.inputs)
        connector = connector_cls(**connector_kwargs)
        self._set_cached_client("connector", connector, **cache_kwargs)
        return connector

    # -------------------------------------------------------------------------
    # AWS
    # -------------------------------------------------------------------------

    def get_aws_connector(
        self,
        execution_role_arn: str | None = None,
    ) -> AWSConnector:
        """Get a cached AWSConnector instance.

        Requires: pip install extended-data[aws]
        """
        try:
            from extended_data.connectors.aws import AWSConnector
        except ImportError as e:
            msg = "AWS connector requires boto3. Install with: pip install extended-data[aws]"
            raise ImportError(msg) from e

        execution_role_arn = execution_role_arn or self.get_input("EXECUTION_ROLE_ARN", required=False)

        cached = self._get_cached_client("aws_connector", execution_role_arn=execution_role_arn)
        if cached:
            return cached

        connector = AWSConnector(
            execution_role_arn=execution_role_arn,
            logger=self.logging,
            inputs=self.inputs,
        )
        self._set_cached_client("aws_connector", connector, execution_role_arn=execution_role_arn)
        return connector

    def get_aws_client(
        self,
        client_name: str,
        execution_role_arn: str | None = None,
        role_session_name: str | None = None,
        config: Config | None = None,
        **client_args: Any,
    ) -> boto3.client:
        """Get a cached boto3 client."""
        execution_role_arn = execution_role_arn or self.get_input("EXECUTION_ROLE_ARN", required=False)
        role_session_name = role_session_name or self.get_input("ROLE_SESSION_NAME", required=False)

        cached = self._get_cached_client(
            "aws_client",
            client_name=client_name,
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
        )
        if cached:
            return cached

        connector = self.get_aws_connector(execution_role_arn)
        client = connector.get_aws_client(
            client_name=client_name,
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
            config=config,
            **client_args,
        )
        self._set_cached_client(
            "aws_client",
            client,
            client_name=client_name,
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
        )
        return client

    def get_aws_resource(
        self,
        service_name: str,
        execution_role_arn: str | None = None,
        role_session_name: str | None = None,
        config: Config | None = None,
        **resource_args: Any,
    ) -> ServiceResource:
        """Get a cached boto3 resource."""
        execution_role_arn = execution_role_arn or self.get_input("EXECUTION_ROLE_ARN", required=False)
        role_session_name = role_session_name or self.get_input("ROLE_SESSION_NAME", required=False)

        cached = self._get_cached_client(
            "aws_resource",
            service_name=service_name,
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
        )
        if cached:
            return cached

        connector = self.get_aws_connector(execution_role_arn)
        resource = connector.get_aws_resource(
            service_name=service_name,
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
            config=config,
            **resource_args,
        )
        self._set_cached_client(
            "aws_resource",
            resource,
            service_name=service_name,
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
        )
        return resource

    def get_aws_session(
        self,
        execution_role_arn: str | None = None,
        role_session_name: str | None = None,
    ) -> boto3.Session:
        """Get a cached boto3 session."""
        execution_role_arn = execution_role_arn or self.get_input("EXECUTION_ROLE_ARN", required=False)
        role_session_name = role_session_name or self.get_input("ROLE_SESSION_NAME", required=False)

        cached = self._get_cached_client(
            "aws_session",
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
        )
        if cached:
            return cached

        connector = self.get_aws_connector(execution_role_arn)
        session = connector.get_aws_session(
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
        )
        self._set_cached_client(
            "aws_session",
            session,
            execution_role_arn=execution_role_arn,
            role_session_name=role_session_name,
        )
        return session

    # -------------------------------------------------------------------------
    # GitHub
    # -------------------------------------------------------------------------

    def get_github_client(
        self,
        github_owner: str | None = None,
        github_repo: str | None = None,
        github_branch: str | None = None,
        github_token: str | None = None,
    ) -> GitHubConnector:
        """Get a cached GitHubConnector instance.

        Requires: pip install extended-data[github]
        """
        try:
            from extended_data.connectors.github import GitHubConnector
        except ImportError as e:
            msg = "GitHub connector requires PyGithub. Install with: pip install extended-data[github]"
            raise ImportError(msg) from e

        github_owner = github_owner or self.get_input("GITHUB_OWNER", required=True)
        github_repo = github_repo or self.get_input("GITHUB_REPO", required=False)
        github_branch = github_branch or self.get_input("GITHUB_BRANCH", required=False)
        github_token = github_token or self.get_input("GITHUB_TOKEN", required=True)

        cached = self._get_cached_client(
            "github",
            github_owner=github_owner,
            github_repo=github_repo,
            github_branch=github_branch,
            github_token=github_token,
        )
        if cached:
            return cached

        connector = GitHubConnector(
            github_owner=github_owner,
            github_repo=github_repo,
            github_branch=github_branch,
            github_token=github_token,
            logger=self.logging,
            inputs=self.inputs,
        )
        self._set_cached_client(
            "github",
            connector,
            github_owner=github_owner,
            github_repo=github_repo,
            github_branch=github_branch,
            github_token=github_token,
        )
        return connector

    # -------------------------------------------------------------------------
    # Google
    # -------------------------------------------------------------------------

    def get_google_client(
        self,
        service_account_info: dict[str, Any] | str | None = None,
        scopes: list[str] | None = None,
        subject: str | None = None,
    ) -> GoogleConnector:
        """Get a cached GoogleConnector instance.

        Requires: pip install extended-data[google]
        """
        try:
            from extended_data.connectors.google import GoogleConnector
        except ImportError as e:
            msg = (
                "Google connector requires google-api-python-client. "
                "Install with: pip install extended-data[google]"
            )
            raise ImportError(msg) from e

        service_account_info = service_account_info or self.get_input("GOOGLE_SERVICE_ACCOUNT", required=True)

        # For caching, use a hash to avoid exposing sensitive data
        cache_sa = hashlib.sha256(str(service_account_info).encode()).hexdigest()[:16] if service_account_info else None

        cached = self._get_cached_client(
            "google",
            service_account=cache_sa,
            subject=subject,
        )
        if cached:
            return cached

        connector = GoogleConnector(
            service_account_info=service_account_info,
            scopes=scopes,
            subject=subject,
            logger=self.logging,
            inputs=self.inputs,
        )
        self._set_cached_client(
            "google",
            connector,
            service_account=cache_sa,
            subject=subject,
        )
        return connector

    # -------------------------------------------------------------------------
    # Slack
    # -------------------------------------------------------------------------

    def get_slack_client(
        self,
        token: str | None = None,
        bot_token: str | None = None,
    ) -> SlackConnector:
        """Get a cached SlackConnector instance.

        Requires: pip install extended-data[slack]
        """
        try:
            from extended_data.connectors.slack import SlackConnector
        except ImportError as e:
            msg = "Slack connector requires slack_sdk. Install with: pip install extended-data[slack]"
            raise ImportError(msg) from e

        token = token or self.get_input("SLACK_TOKEN", required=True)
        bot_token = bot_token or self.get_input("SLACK_BOT_TOKEN", required=True)

        cached = self._get_cached_client("slack", token=token, bot_token=bot_token)
        if cached:
            return cached

        connector = SlackConnector(
            token=token,
            bot_token=bot_token,
            logger=self.logging,
            inputs=self.inputs,
        )
        self._set_cached_client("slack", connector, token=token, bot_token=bot_token)
        return connector

    # -------------------------------------------------------------------------
    # Vault
    # -------------------------------------------------------------------------

    def get_vault_client(
        self,
        vault_url: str | None = None,
        vault_namespace: str | None = None,
        vault_token: str | None = None,
    ) -> hvac.Client:
        """Get a cached Vault hvac.Client instance.

        Requires: pip install extended-data[vault]
        """
        try:
            from extended_data.connectors.vault import VaultConnector
        except ImportError as e:
            msg = "Vault connector requires hvac. Install with: pip install extended-data[vault]"
            raise ImportError(msg) from e

        vault_url = vault_url or self.get_input("VAULT_ADDR", required=False)
        vault_namespace = vault_namespace or self.get_input("VAULT_NAMESPACE", required=False)
        vault_token = vault_token or self.get_input("VAULT_TOKEN", required=False)

        cached = self._get_cached_client(
            "vault",
            vault_url=vault_url,
            vault_namespace=vault_namespace,
            vault_token=vault_token,
        )
        if cached:
            return cached

        connector = VaultConnector(
            vault_url=vault_url,
            vault_namespace=vault_namespace,
            vault_token=vault_token,
            logger=self.logging,
            inputs=self.inputs,
        )
        client = connector.vault_client
        self._set_cached_client(
            "vault",
            client,
            vault_url=vault_url,
            vault_namespace=vault_namespace,
            vault_token=vault_token,
        )
        return client

    def get_vault_connector(
        self,
        vault_url: str | None = None,
        vault_namespace: str | None = None,
        vault_token: str | None = None,
    ) -> VaultConnector:
        """Get a cached VaultConnector instance.

        Requires: pip install extended-data[vault]
        """
        try:
            from extended_data.connectors.vault import VaultConnector
        except ImportError as e:
            msg = "Vault connector requires hvac. Install with: pip install extended-data[vault]"
            raise ImportError(msg) from e

        vault_url = vault_url or self.get_input("VAULT_ADDR", required=False)
        vault_namespace = vault_namespace or self.get_input("VAULT_NAMESPACE", required=False)
        vault_token = vault_token or self.get_input("VAULT_TOKEN", required=False)

        cached = self._get_cached_client(
            "vault_connector",
            vault_url=vault_url,
            vault_namespace=vault_namespace,
            vault_token=vault_token,
        )
        if cached:
            return cached

        connector = VaultConnector(
            vault_url=vault_url,
            vault_namespace=vault_namespace,
            vault_token=vault_token,
            logger=self.logging,
            inputs=self.inputs,
        )
        self._set_cached_client(
            "vault_connector",
            connector,
            vault_url=vault_url,
            vault_namespace=vault_namespace,
            vault_token=vault_token,
        )
        return connector

    # -------------------------------------------------------------------------
    # Zoom
    # -------------------------------------------------------------------------

    def get_zoom_client(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        account_id: str | None = None,
    ) -> ZoomConnector:
        """Get a cached ZoomConnector instance."""
        client_id = client_id or self.get_input("ZOOM_CLIENT_ID", required=True)
        client_secret = client_secret or self.get_input("ZOOM_CLIENT_SECRET", required=True)
        account_id = account_id or self.get_input("ZOOM_ACCOUNT_ID", required=True)

        cached = self._get_cached_client(
            "zoom",
            client_id=client_id,
            client_secret=client_secret,
            account_id=account_id,
        )
        if cached:
            return cached

        connector = ZoomConnector(
            client_id=client_id,
            client_secret=client_secret,
            account_id=account_id,
            logger=self.logging,
            inputs=self.inputs,
        )
        self._set_cached_client(
            "zoom",
            connector,
            client_id=client_id,
            client_secret=client_secret,
            account_id=account_id,
        )
        return connector
