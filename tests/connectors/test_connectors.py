"""Tests for ConnectorFabric main class."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from extended_data.connectors import registry
from extended_data.connectors.connectors import ConnectorFabric
from extended_data.connectors.registry import _register_builtins


# Helper to check if optional dependencies are available
def _has_module(name: str) -> bool:
    """Check if a module can be imported."""
    try:
        __import__(name)
        return True
    except ImportError:
        return False


# Skip markers for optional dependencies
requires_boto3 = pytest.mark.skipif(not _has_module("boto3"), reason="boto3 not installed")
requires_google = pytest.mark.skipif(
    not _has_module("googleapiclient"), reason="google-api-python-client not installed"
)
requires_github = pytest.mark.skipif(not _has_module("github"), reason="PyGithub not installed")
requires_slack = pytest.mark.skipif(not _has_module("slack_sdk"), reason="slack-sdk not installed")
requires_vault = pytest.mark.skipif(not _has_module("hvac"), reason="hvac not installed")


class TestConnectorFabric:
    """Tests for ConnectorFabric class."""

    def test_init(self):
        """Test ConnectorFabric initialization."""
        vc = ConnectorFabric()
        assert vc.logger is not None
        assert vc._client_cache is not None

    def test_init_with_logger(self):
        """Test ConnectorFabric initialization with custom logger."""
        mock_logger = MagicMock()
        vc = ConnectorFabric(logger=mock_logger)
        assert vc.logging == mock_logger
        assert vc.logger is not None  # Logger is extracted from logging

    def test_get_cache_key(self):
        """Test cache key generation."""
        vc = ConnectorFabric()
        key1 = vc._get_cache_key(param1="value1", param2="value2")
        key2 = vc._get_cache_key(param1="value1", param2="value2")
        key3 = vc._get_cache_key(param1="value1", param2="different")

        assert key1 == key2
        assert key1 != key3

    def test_cache_client(self):
        """Test caching and retrieving clients."""
        vc = ConnectorFabric()
        mock_client = MagicMock()

        # Set cache
        vc._set_cached_client("test_type", mock_client, param="value")

        # Get from cache
        cached = vc._get_cached_client("test_type", param="value")
        assert cached == mock_client

        # Different params should return None
        cached = vc._get_cached_client("test_type", param="different")
        assert cached is None

    @patch("extended_data.connectors.connectors.get_connector_class")
    def test_get_connector_uses_registry_with_shared_context(self, mock_get_connector_class):
        """Generic connector lookup injects shared fabric inputs and logging."""

        class DummyConnector:
            def __init__(self, *, logger, inputs, token):
                self.logger = logger
                self.inputs = inputs
                self.token = token

        vc = ConnectorFabric(inputs={"TOKEN": "from-inputs"}, from_environment=False)
        mock_get_connector_class.return_value = DummyConnector

        connector = vc.get_connector(" dummy ", token="direct-token")

        assert isinstance(connector, DummyConnector)
        assert connector.logger is vc.logging
        assert connector.inputs is vc.inputs
        assert connector.token == "direct-token"
        mock_get_connector_class.assert_called_once_with("dummy")

    @patch("extended_data.connectors.connectors.get_connector_class")
    def test_get_connector_preserves_explicit_context_overrides(self, mock_get_connector_class):
        """Generic connector lookup lets callers override injected fabric context."""

        class DummyConnector:
            def __init__(self, *, logger, inputs):
                self.logger = logger
                self.inputs = inputs

        custom_logger = MagicMock()
        custom_inputs = {"TOKEN": "custom"}
        vc = ConnectorFabric(inputs={"TOKEN": "fabric"}, from_environment=False)
        mock_get_connector_class.return_value = DummyConnector

        connector = vc.get_connector("dummy", logger=custom_logger, inputs=custom_inputs)

        assert connector.logger is custom_logger
        assert connector.inputs is custom_inputs

    @patch("extended_data.connectors.connectors.get_connector_class")
    def test_get_connector_caches_by_name_and_kwargs(self, mock_get_connector_class):
        """Generic connectors are cached independently by name and constructor args."""

        class DummyConnector:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        vc = ConnectorFabric(from_environment=False)
        mock_get_connector_class.return_value = DummyConnector

        first = vc.get_connector("dummy", token="one")
        second = vc.get_connector(" DUMMY ", token="one")
        third = vc.get_connector("dummy", token="two")

        assert first is second
        assert third is not first
        assert mock_get_connector_class.call_count == 2

    def test_connector_fabric_exposes_catalog_info(self):
        """ConnectorFabric exposes registry-backed catalog metadata."""
        vc = ConnectorFabric(from_environment=False)

        info = vc.list_connector_info()
        names = {connector["name"] for connector in info}

        assert "cursor" in names
        assert "github" in names
        assert vc.get_connector_info(" github ")["name"] == "github"
        assert isinstance(vc.list_connectors(), dict)

    @requires_boto3
    @patch("extended_data.connectors.aws.AWSConnector")
    def test_get_aws_connector(self, mock_aws):
        """Test getting AWS connector."""
        vc = ConnectorFabric()
        mock_connector = MagicMock()
        mock_aws.return_value = mock_connector

        result = vc.get_aws_connector(execution_role_arn="arn:aws:iam::123456789012:role/TestRole")

        assert result == mock_connector
        mock_aws.assert_called_once()

    @requires_boto3
    @patch("extended_data.connectors.aws.AWSConnector")
    def test_get_aws_connector_caching(self, mock_aws):
        """Test AWS connector caching."""
        vc = ConnectorFabric()
        mock_connector = MagicMock()
        mock_aws.return_value = mock_connector

        # First call
        result1 = vc.get_aws_connector(execution_role_arn="arn:aws:iam::123456789012:role/TestRole")
        # Second call with same params
        result2 = vc.get_aws_connector(execution_role_arn="arn:aws:iam::123456789012:role/TestRole")

        assert result1 == result2
        # Should only create connector once
        mock_aws.assert_called_once()

    @requires_boto3
    @patch("extended_data.connectors.aws.AWSConnector")
    def test_get_aws_client(self, mock_aws):
        """Test getting AWS client."""
        vc = ConnectorFabric()
        mock_connector = MagicMock()
        mock_client = MagicMock()
        mock_connector.get_aws_client.return_value = mock_client
        mock_aws.return_value = mock_connector

        result = vc.get_aws_client("s3")

        assert result == mock_client
        mock_connector.get_aws_client.assert_called_once()

    @requires_boto3
    @patch("extended_data.connectors.aws.AWSConnector")
    def test_get_aws_resource(self, mock_aws):
        """Test getting AWS resource."""
        vc = ConnectorFabric()
        mock_connector = MagicMock()
        mock_resource = MagicMock()
        mock_connector.get_aws_resource.return_value = mock_resource
        mock_aws.return_value = mock_connector

        result = vc.get_aws_resource("s3")

        assert result == mock_resource
        mock_connector.get_aws_resource.assert_called_once()

    @requires_google
    @patch("extended_data.connectors.google.GoogleConnector")
    def test_get_google_client(self, mock_google):
        """Test getting Google client."""
        vc = ConnectorFabric(
            inputs={"GOOGLE_SERVICE_ACCOUNT": '{"type": "service_account"}', "GOOGLE_PROJECT_ID": "test-project"}
        )
        mock_connector = MagicMock()
        mock_client = MagicMock()
        mock_connector.get_service.return_value = mock_client
        mock_google.return_value = mock_connector

        result = vc.get_google_client()

        assert result == mock_connector

    @requires_github
    @patch("extended_data.connectors.github.GitHubConnector")
    def test_get_github_client(self, mock_github):
        """Test getting GitHub client."""
        vc = ConnectorFabric(inputs={"GITHUB_OWNER": "test-org", "GITHUB_TOKEN": "ghp_test123"})
        mock_connector = MagicMock()
        mock_github.return_value = mock_connector

        result = vc.get_github_client()

        assert result == mock_connector

    @requires_slack
    @patch("extended_data.connectors.slack.SlackConnector")
    def test_get_slack_client(self, mock_slack):
        """Test getting Slack client."""
        vc = ConnectorFabric(inputs={"SLACK_TOKEN": "xoxp-test123", "SLACK_BOT_TOKEN": "xoxb-test123"})
        mock_connector = MagicMock()
        mock_slack.return_value = mock_connector

        result = vc.get_slack_client()

        assert result == mock_connector

    @requires_vault
    @patch("extended_data.connectors.vault.VaultConnector")
    def test_get_vault_connector(self, mock_vault):
        """Test getting Vault connector."""
        vc = ConnectorFabric()
        mock_connector = MagicMock()
        mock_vault.return_value = mock_connector

        result = vc.get_vault_connector(vault_token="hvs.test123")

        assert result == mock_connector

    @patch("extended_data.connectors.connectors.ZoomConnector")
    def test_get_zoom_client(self, mock_zoom):
        """Test getting Zoom client."""
        vc = ConnectorFabric(
            inputs={
                "ZOOM_CLIENT_ID": "test-client-id",
                "ZOOM_CLIENT_SECRET": "test-secret",
                "ZOOM_ACCOUNT_ID": "test-account",
            }
        )
        mock_connector = MagicMock()
        mock_zoom.return_value = mock_connector

        result = vc.get_zoom_client()

        assert result == mock_connector

    @requires_vault
    @patch("extended_data.connectors.vault.VaultConnector")
    def test_get_vault_client(self, mock_vault):
        """Test getting Vault client."""
        vc = ConnectorFabric()
        mock_connector = MagicMock()
        mock_client = MagicMock()
        mock_connector.vault_client = mock_client
        mock_vault.return_value = mock_connector

        result = vc.get_vault_client(vault_token="hvs.test123")

        assert result == mock_client

    @requires_boto3
    @requires_slack
    def test_multiple_connector_types_cached_separately(self):
        """Test that different connector types are cached separately."""
        with (
            patch("extended_data.connectors.aws.AWSConnector") as mock_aws,
            patch("extended_data.connectors.slack.SlackConnector") as mock_slack,
        ):
            vc = ConnectorFabric(inputs={"SLACK_TOKEN": "xoxp-test123", "SLACK_BOT_TOKEN": "xoxb-test123"})
            mock_aws_connector = MagicMock()
            mock_slack_connector = MagicMock()
            mock_aws.return_value = mock_aws_connector
            mock_slack.return_value = mock_slack_connector

            aws1 = vc.get_aws_connector()
            slack1 = vc.get_slack_client()
            _aws2 = vc.get_aws_connector()
            _slack2 = vc.get_slack_client()

            # Each connector type should only be created once
            mock_aws.assert_called_once()
            mock_slack.assert_called_once()

            # But they should be different objects
            assert aws1 != slack1

    def test_get_aws_connector_without_boto3(self):
        """Test that get_aws_connector raises ImportError without boto3."""
        # This test runs even without boto3 to verify error handling
        vc = ConnectorFabric()
        if not _has_module("boto3"):
            with pytest.raises(ImportError, match="boto3"):
                vc.get_aws_connector()

    def test_get_github_client_without_pygithub(self):
        """Test that get_github_client raises ImportError without PyGithub."""
        vc = ConnectorFabric(inputs={"GITHUB_OWNER": "test-org", "GITHUB_TOKEN": "ghp_test123"})
        if not _has_module("github"):
            with pytest.raises(ImportError, match="PyGithub"):
                vc.get_github_client()

    def test_get_connector_class_known_missing_builtin_has_install_hint(self, monkeypatch):
        """Registry raises install guidance when a known built-in extra is missing."""
        monkeypatch.setattr(registry, "_connector_cache", {})
        monkeypatch.setitem(
            registry._missing_builtin_connectors,
            "github",
            ImportError("No module named 'github'"),
        )

        with pytest.raises(ImportError, match=r"extended-data\[github\]"):
            registry.get_connector_class(" github ")

    def test_get_connector_info_includes_known_missing_builtin(self, monkeypatch):
        """Registry metadata includes unavailable known connectors."""
        monkeypatch.setattr(registry, "_connector_cache", {})
        monkeypatch.setitem(
            registry._missing_builtin_connectors,
            "github",
            ImportError("No module named 'github'"),
        )

        info = registry.get_connector_info(" github ")

        assert info["name"] == "github"
        assert info["available"] is False
        assert info["extra"] == "github"
        assert info["install"] == "pip install extended-data[github]"
        assert info["class"] == "GitHubConnector"

    def test_lazy_builtin_with_missing_requirements_is_unavailable(self):
        """Lazy-loadable built-ins still report unavailable when extras are missing."""
        registry.clear_cache()

        if not _has_module("boto3"):
            info = registry.get_connector_info("aws")

            assert info["available"] is False
            assert info["missing"] == ["boto3"]

            with pytest.raises(ImportError, match=r"extended-data\[aws\]"):
                registry.get_connector_class("aws")

    def test_available_only_catalog_filters_missing_lazy_builtins(self):
        """Available-only metadata excludes lazy built-ins with missing extras."""
        registry.clear_cache()

        info = registry.list_connector_info(include_unavailable=False)

        assert all(connector["available"] for connector in info)

    def test_register_builtins_tracks_missing_optional_dependency(self, monkeypatch):
        """Built-in discovery remembers optional dependency import failures."""
        monkeypatch.setattr(registry, "_missing_builtin_connectors", {})

        def fake_import_module(module_path):
            if module_path == "extended_data.connectors.github":
                raise ImportError("No module named 'github'")
            return SimpleNamespace()

        monkeypatch.setattr("importlib.import_module", fake_import_module)

        _register_builtins({})

        assert "github" in registry._missing_builtin_connectors

    def test_register_builtins_includes_specialized_google_connectors(self):
        """Registry builtins expose the advertised specialized Google connectors."""
        pytest.importorskip("googleapiclient")
        connectors = {}

        _register_builtins(connectors)

        assert connectors["google"].__name__ == "GoogleConnector"
        assert connectors["google_cloud"].__name__ == "GoogleCloudConnector"
        assert connectors["google_workspace"].__name__ == "GoogleWorkspaceConnector"
        assert connectors["google_billing"].__name__ == "GoogleBillingConnector"

    def test_register_builtins_loads_github_entrypoint_name(self):
        """Registry builtins keep the GitHub connector spelling compatible with entry points."""
        pytest.importorskip("github")
        connectors = {}

        _register_builtins(connectors)

        assert connectors["github"].__name__ == "GitHubConnector"
