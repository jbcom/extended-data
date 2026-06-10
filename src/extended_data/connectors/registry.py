"""Vendor Connector Registry with Entry Points.

This module provides automatic discovery and registration of extended data connectors
using Python's entry points system. This allows:

1. DRY interface via VendorConnectorBase ABC
2. Automatic discovery of all connectors (even from other packages)
3. Unified factory function for instantiation
4. Same registry used by both MCP and CLI

Usage:
    from extended_data.connectors.registry import get_connector, list_connectors

    # List available connectors
    available = list_connectors()
    # {'jules': <class JulesConnector>, 'cursor': <class CursorConnector>, ...}

    # Get a specific connector instance
    connector = get_connector('jules', api_key='...')

    # Use it
    sources = connector.list_sources()

Entry Points (in pyproject.toml):
    [project.entry-points."extended_data.connectors"]
    jules = "extended_data.connectors.google.jules:JulesConnector"
    cursor = "extended_data.connectors.cursor:CursorConnector"
    github = "extended_data.connectors.github:GitHubConnector"
"""

from __future__ import annotations

import builtins

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from extended_data.connectors.base import VendorConnectorBase

# Cache for discovered connectors
_connector_cache: dict[str, builtins.type[VendorConnectorBase]] | None = None


def _discover_connectors() -> dict[str, builtins.type[VendorConnectorBase]]:
    """Discover all registered connectors via entry points."""
    global _connector_cache

    if _connector_cache is not None:
        return _connector_cache

    connectors: dict[str, builtins.type[VendorConnectorBase]] = {}

    # Python 3.10+ uses importlib.metadata
    from importlib.metadata import entry_points

    eps = entry_points(group="extended_data.connectors")

    for ep in eps:
        try:
            connectors[ep.name] = ep.load()
        except Exception as e:
            # Log but don't fail - allow partial loading
            import warnings

            warnings.warn(f"Failed to load connector '{ep.name}': {e}", stacklevel=2)

    # Also include built-in connectors not yet in entry points
    # (for development/transition period)
    _register_builtins(connectors)

    _connector_cache = connectors
    return connectors


def _register_builtins(connectors: dict[str, builtins.type[VendorConnectorBase]]) -> None:
    """Register built-in connectors that may not be in entry points yet."""
    builtin_connectors = {
        # Google connectors
        "jules": ("extended_data.connectors.google.jules", "JulesConnector"),
        "google": ("extended_data.connectors.google", "GoogleConnector"),
        "google_cloud": ("extended_data.connectors.google", "GoogleCloudConnector"),
        "google_workspace": ("extended_data.connectors.google", "GoogleWorkspaceConnector"),
        "google_billing": ("extended_data.connectors.google", "GoogleBillingConnector"),
        # Other connectors
        "cursor": ("extended_data.connectors.cursor", "CursorConnector"),
        "github": ("extended_data.connectors.github", "GitHubConnector"),
        "meshy": ("extended_data.connectors.meshy", "MeshyConnector"),
        "anthropic": ("extended_data.connectors.anthropic", "AnthropicConnector"),
        "aws": ("extended_data.connectors.aws", "AWSConnector"),
        "slack": ("extended_data.connectors.slack", "SlackConnector"),
        "zoom": ("extended_data.connectors.zoom", "ZoomConnector"),
        "vault": ("extended_data.connectors.vault", "VaultConnector"),
    }

    for name, (module_path, class_name) in builtin_connectors.items():
        if name in connectors:
            continue  # Entry point takes precedence
        try:
            import importlib

            module = importlib.import_module(module_path)
            cls = getattr(module, class_name, None)
            if cls is not None:
                connectors[name] = cls
        except (ImportError, AttributeError):
            pass  # Optional dependency not installed


def list_connectors() -> dict[str, builtins.type[VendorConnectorBase]]:
    """List all available connectors.

    Returns:
        Dict mapping connector name to connector class.
    """
    return _discover_connectors().copy()


def get_connector_class(name: str) -> builtins.type[VendorConnectorBase]:
    """Get a connector class by name.

    Args:
        name: Connector name (e.g., 'jules', 'cursor', 'github')

    Returns:
        The connector class.

    Raises:
        ValueError: If connector not found.
    """
    connectors = _discover_connectors()
    name_lower = name.lower()

    if name_lower not in connectors:
        available = ", ".join(sorted(connectors.keys()))
        raise ValueError(f"Unknown connector: {name}. Available: {available}")

    return connectors[name_lower]


def get_connector(name: str, **kwargs: Any) -> VendorConnectorBase:
    """Factory to instantiate a connector by name.

    Args:
        name: Connector name (e.g., 'jules', 'cursor', 'github')
        **kwargs: Arguments passed to connector constructor

    Returns:
        Instantiated connector.

    Raises:
        ValueError: If connector not found.

    Example:
        >>> connector = get_connector('jules', api_key='...')
        >>> connector.list_sources()
    """
    cls = get_connector_class(name)
    return cls(**kwargs)


def clear_cache() -> None:
    """Clear the connector cache (useful for testing)."""
    global _connector_cache
    _connector_cache = None


# =============================================================================
# Connector Info Helpers
# =============================================================================


def get_connector_info(name: str) -> dict[str, Any]:
    """Get metadata about a connector.

    Returns:
        Dict with name, module, env_vars, description, etc.
    """
    cls = get_connector_class(name)

    return {
        "name": name,
        "class": cls.__name__,
        "module": cls.__module__,
        "base_url": getattr(cls, "BASE_URL", None),
        "api_key_env": getattr(cls, "API_KEY_ENV", None),
        "description": cls.__doc__.split("\n")[0] if cls.__doc__ else None,
    }


def list_connector_info() -> list[dict[str, Any]]:
    """Get metadata for all connectors."""
    return [get_connector_info(name) for name in sorted(list_connectors().keys())]
