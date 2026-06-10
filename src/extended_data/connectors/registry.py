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

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, NoReturn

from extended_data.connectors._optional import (
    get_connector_install_command,
    get_connector_requirements,
    get_extra_for_connector,
    get_missing_connector_requirements,
)


if TYPE_CHECKING:
    from extended_data.connectors.base import VendorConnectorBase


@dataclass(frozen=True)
class BuiltinConnectorSpec:
    """Import metadata for a built-in connector."""

    module_path: str
    class_name: str
    extra: str


@dataclass(frozen=True)
class ConnectorInfo:
    """Registry metadata for a connector."""

    name: str
    available: bool
    source: str
    extra: str | None
    install: str | None
    requirements: tuple[str, ...]
    missing: tuple[str, ...]
    class_name: str | None
    module: str | None
    base_url: str | None
    api_key_env: str | None
    description: str | None
    error: str | None

    def as_dict(self) -> dict[str, Any]:
        """Return JSON-friendly connector metadata."""
        return {
            "name": self.name,
            "available": self.available,
            "source": self.source,
            "extra": self.extra,
            "install": self.install,
            "requirements": list(self.requirements),
            "missing": list(self.missing),
            "class": self.class_name,
            "module": self.module,
            "base_url": self.base_url,
            "api_key_env": self.api_key_env,
            "description": self.description,
            "error": self.error,
        }


BUILTIN_CONNECTORS: dict[str, BuiltinConnectorSpec] = {
    # Google connectors
    "jules": BuiltinConnectorSpec("extended_data.connectors.google.jules", "JulesConnector", "google"),
    "google": BuiltinConnectorSpec("extended_data.connectors.google", "GoogleConnector", "google"),
    "google_cloud": BuiltinConnectorSpec("extended_data.connectors.google", "GoogleCloudConnector", "google"),
    "google_workspace": BuiltinConnectorSpec("extended_data.connectors.google", "GoogleWorkspaceConnector", "google"),
    "google_billing": BuiltinConnectorSpec("extended_data.connectors.google", "GoogleBillingConnector", "google"),
    # Other connectors
    "cursor": BuiltinConnectorSpec("extended_data.connectors.cursor", "CursorConnector", "cursor"),
    "github": BuiltinConnectorSpec("extended_data.connectors.github", "GitHubConnector", "github"),
    "meshy": BuiltinConnectorSpec("extended_data.connectors.meshy", "MeshyConnector", "meshy"),
    "secrets": BuiltinConnectorSpec("extended_data.connectors.secrets", "SecretsConnector", "secrets"),
    "anthropic": BuiltinConnectorSpec("extended_data.connectors.anthropic", "AnthropicConnector", "anthropic"),
    "aws": BuiltinConnectorSpec("extended_data.connectors.aws", "AWSConnector", "aws"),
    "slack": BuiltinConnectorSpec("extended_data.connectors.slack", "SlackConnector", "slack"),
    "zoom": BuiltinConnectorSpec("extended_data.connectors.zoom", "ZoomConnector", "zoom"),
    "vault": BuiltinConnectorSpec("extended_data.connectors.vault", "VaultConnector", "vault"),
}


# Cache for discovered connectors
_connector_cache: dict[str, builtins.type[VendorConnectorBase]] | None = None
_missing_builtin_connectors: dict[str, ImportError] = {}


def _normalize_connector_name(name: str) -> str:
    """Normalize connector registry names."""
    return name.strip().lower()


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
        connector_name = _normalize_connector_name(ep.name)
        try:
            connectors[connector_name] = ep.load()
            _missing_builtin_connectors.pop(connector_name, None)
        except ImportError as e:
            if connector_name in BUILTIN_CONNECTORS:
                _missing_builtin_connectors[connector_name] = e
                continue
            import warnings

            warnings.warn(f"Failed to load connector '{ep.name}': {e}", stacklevel=2)
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
    for name, spec in BUILTIN_CONNECTORS.items():
        if name in connectors:
            _missing_builtin_connectors.pop(name, None)
            continue  # Entry point takes precedence
        try:
            import importlib

            module = importlib.import_module(spec.module_path)
            cls = getattr(module, spec.class_name, None)
            if cls is not None:
                connectors[name] = cls
                _missing_builtin_connectors.pop(name, None)
            else:
                _missing_builtin_connectors[name] = ImportError(
                    f"Could not find {spec.class_name} in {spec.module_path}"
                )
        except ImportError as e:
            _missing_builtin_connectors[name] = e  # Optional dependency not installed


def _raise_missing_builtin_connector(name: str, error: ImportError) -> NoReturn:
    """Raise a clear install hint for a known built-in connector."""
    install = get_connector_install_command(name) or f"pip install extended-data[{BUILTIN_CONNECTORS[name].extra}]"
    missing = get_missing_connector_requirements(name)
    msg = (
        f"The '{name}' connector is built in but its optional dependencies are not installed.\n"
        f"Install with: {install}"
    )
    if missing:
        msg = f"{msg}\nMissing packages: {', '.join(missing)}"
    if str(error):
        msg = f"{msg}\nOriginal import error: {error}"
    raise ImportError(msg) from error


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
    name_lower = _normalize_connector_name(name)

    if name_lower not in connectors:
        if name_lower in _missing_builtin_connectors:
            _raise_missing_builtin_connector(name_lower, _missing_builtin_connectors[name_lower])
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
    _missing_builtin_connectors.clear()


def _get_description(cls: builtins.type[VendorConnectorBase]) -> str | None:
    """Get the first useful line from a connector docstring."""
    if not cls.__doc__:
        return None
    for line in cls.__doc__.splitlines():
        description = line.strip()
        if description:
            return description
    return None


def _available_connector_info(name: str, cls: builtins.type[VendorConnectorBase]) -> ConnectorInfo:
    """Build metadata for a loadable connector."""
    spec = BUILTIN_CONNECTORS.get(name)
    source = "builtin" if spec else "entry_point"
    extra = spec.extra if spec else get_extra_for_connector(name)
    requirements = tuple(get_connector_requirements(name))
    missing = tuple(get_missing_connector_requirements(name))

    return ConnectorInfo(
        name=name,
        available=True,
        source=source,
        extra=extra,
        install=get_connector_install_command(name),
        requirements=requirements,
        missing=missing,
        class_name=cls.__name__,
        module=cls.__module__,
        base_url=getattr(cls, "BASE_URL", None),
        api_key_env=getattr(cls, "API_KEY_ENV", None),
        description=_get_description(cls),
        error=None,
    )


def _missing_builtin_connector_info(name: str, error: ImportError | None) -> ConnectorInfo:
    """Build metadata for a known built-in connector that cannot be loaded."""
    spec = BUILTIN_CONNECTORS[name]

    return ConnectorInfo(
        name=name,
        available=False,
        source="builtin",
        extra=spec.extra,
        install=get_connector_install_command(name),
        requirements=tuple(get_connector_requirements(name)),
        missing=tuple(get_missing_connector_requirements(name)),
        class_name=spec.class_name,
        module=spec.module_path,
        base_url=None,
        api_key_env=None,
        description=None,
        error=str(error) if error else "Connector class could not be loaded.",
    )


# =============================================================================
# Connector Info Helpers
# =============================================================================


def get_connector_info(name: str, *, include_unavailable: bool = True) -> dict[str, Any]:
    """Get registry metadata about a connector."""
    connector_name = _normalize_connector_name(name)
    connectors = _discover_connectors()

    if connector_name in connectors:
        return _available_connector_info(connector_name, connectors[connector_name]).as_dict()

    if connector_name in _missing_builtin_connectors:
        if include_unavailable:
            return _missing_builtin_connector_info(connector_name, _missing_builtin_connectors[connector_name]).as_dict()
        _raise_missing_builtin_connector(connector_name, _missing_builtin_connectors[connector_name])

    if include_unavailable and connector_name in BUILTIN_CONNECTORS:
        return _missing_builtin_connector_info(connector_name, None).as_dict()

    available = ", ".join(sorted(connectors.keys()))
    raise ValueError(f"Unknown connector: {name}. Available: {available}")


def list_connector_info(*, include_unavailable: bool = True) -> list[dict[str, Any]]:
    """Get registry metadata for known connectors."""
    connectors = _discover_connectors()
    names = set(connectors)
    if include_unavailable:
        names.update(BUILTIN_CONNECTORS)
        names.update(_missing_builtin_connectors)
    return [get_connector_info(name, include_unavailable=include_unavailable) for name in sorted(names)]
