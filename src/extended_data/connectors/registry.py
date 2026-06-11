"""Connector Registry with Entry Points.

This module provides automatic discovery and registration of extended data connectors
using Python's entry points system. This allows:

1. DRY interface via ConnectorBase ABC
2. Automatic discovery of all connectors (even from other packages)
3. Unified factory function for instantiation
4. Same registry used by both MCP and CLI

Usage:
    from extended_data.connectors.registry import get_connector, list_connectors

    # List available connectors
    available = list_connectors()
    # ExtendedList(["anthropic", "aws", "cursor", ...])

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
from extended_data.containers import ExtendedDict, ExtendedList, ExtendedString, extend_data
from extended_data.primitives.redaction import redact_sensitive_text


if TYPE_CHECKING:
    from extended_data.connectors.base import ConnectorBase


@dataclass(frozen=True)
class BuiltinConnectorSpec:
    """Import metadata for a built-in connector."""

    module_path: str
    class_name: str
    extra: str
    category: str = "external"
    capabilities: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConnectorInfo:
    """Registry metadata for a connector."""

    name: str
    available: bool
    source: str
    extra: str | None
    category: str
    capabilities: tuple[str, ...]
    install: str | None
    requirements: tuple[str, ...]
    missing: tuple[str, ...]
    class_name: str | None
    module: str | None
    base_url: str | None
    description: str | None
    error: str | None

    def as_dict(self) -> ExtendedDict:
        """Return extended JSON-friendly connector metadata."""
        return extend_data({
            "name": self.name,
            "available": self.available,
            "source": self.source,
            "extra": self.extra,
            "category": self.category,
            "capabilities": list(self.capabilities),
            "install": self.install,
            "requirements": list(self.requirements),
            "missing": list(self.missing),
            "class": self.class_name,
            "module": self.module,
            "base_url": self.base_url,
            "description": self.description,
            "error": self.error,
        })


BUILTIN_CONNECTORS: dict[str, BuiltinConnectorSpec] = {
    # Google connectors
    "jules": BuiltinConnectorSpec(
        "extended_data.connectors.google.jules",
        "JulesConnector",
        "google",
        category="ai",
        capabilities=("sources", "sessions"),
    ),
    "google": BuiltinConnectorSpec(
        "extended_data.connectors.google",
        "GoogleConnector",
        "google",
        category="cloud",
        capabilities=("workspace", "cloud", "billing", "services", "iam"),
    ),
    # Other connectors
    "cursor": BuiltinConnectorSpec(
        "extended_data.connectors.cursor",
        "CursorConnector",
        "cursor",
        category="ai",
        capabilities=("agents", "repositories", "models"),
    ),
    "github": BuiltinConnectorSpec(
        "extended_data.connectors.github",
        "GitHubConnector",
        "github",
        category="development",
        capabilities=("repositories", "teams", "files", "graphql", "workflows"),
    ),
    "meshy": BuiltinConnectorSpec(
        "extended_data.connectors.meshy",
        "MeshyConnector",
        "meshy",
        category="media",
        capabilities=("3d-generation", "animation", "rigging", "retexturing", "metadata"),
    ),
    "secrets": BuiltinConnectorSpec(
        "extended_data.connectors.secrets",
        "SecretsConnector",
        "secrets",
        category="secrets",
        capabilities=("pipeline", "dry-run", "merge", "validation"),
    ),
    "anthropic": BuiltinConnectorSpec(
        "extended_data.connectors.anthropic",
        "AnthropicConnector",
        "anthropic",
        category="ai",
        capabilities=("messages", "models", "tools"),
    ),
    "aws": BuiltinConnectorSpec(
        "extended_data.connectors.aws",
        "AWSConnector",
        "aws",
        category="cloud",
        capabilities=("identity", "secrets", "storage", "organizations", "sso"),
    ),
    "slack": BuiltinConnectorSpec(
        "extended_data.connectors.slack",
        "SlackConnector",
        "slack",
        category="communications",
        capabilities=("messages", "channels", "users", "usergroups"),
    ),
    "zoom": BuiltinConnectorSpec(
        "extended_data.connectors.zoom",
        "ZoomConnector",
        "zoom",
        category="communications",
        capabilities=("users", "meetings"),
    ),
    "vault": BuiltinConnectorSpec(
        "extended_data.connectors.vault",
        "VaultConnector",
        "vault",
        category="secrets",
        capabilities=("kv", "aws-iam", "leases"),
    ),
}


# Cache for discovered connectors
_connector_cache: dict[str, builtins.type[ConnectorBase]] | None = None
_missing_builtin_connectors: dict[str, ImportError] = {}


def _normalize_connector_name(name: str) -> str:
    """Normalize connector registry names."""
    return name.strip().lower()


def _normalize_catalog_token(value: object) -> str:
    """Normalize connector catalog categories and capabilities."""
    return str(value).strip().lower().replace("_", "-")


def _discover_connectors() -> dict[str, builtins.type[ConnectorBase]]:
    """Discover all registered connectors via entry points."""
    global _connector_cache

    if _connector_cache is not None:
        return _connector_cache

    connectors: dict[str, builtins.type[ConnectorBase]] = {}

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

            warnings.warn(
                f"Failed to load connector '{redact_sensitive_text(ep.name)}': {redact_sensitive_text(e)}",
                stacklevel=2,
            )
        except Exception as e:
            # Log but don't fail - allow partial loading
            import warnings

            warnings.warn(
                f"Failed to load connector '{redact_sensitive_text(ep.name)}': {redact_sensitive_text(e)}",
                stacklevel=2,
            )

    _connector_cache = connectors
    return connectors


def _raise_missing_builtin_connector(name: str, error: ImportError) -> NoReturn:
    """Raise a clear install hint for a known built-in connector."""
    install = str(get_connector_install_command(name) or f"pip install extended-data[{BUILTIN_CONNECTORS[name].extra}]")
    missing = get_missing_connector_requirements(name)
    msg = (
        f"The '{name}' connector is built in but its optional dependencies are not installed.\n"
        f"Install with: {install}"
    )
    if missing:
        msg = f"{msg}\nMissing packages: {', '.join(str(package) for package in missing)}"
    if str(error):
        msg = f"{msg}\nOriginal import error: {redact_sensitive_text(error)}"
    raise ImportError(msg) from error


def _raise_unregistered_builtin_connector(name: str) -> NoReturn:
    """Raise a packaging error when a declared built-in connector has no entry point."""
    spec = BUILTIN_CONNECTORS[name]
    raise RuntimeError(
        f"The built-in '{name}' connector is declared but is not registered in the "
        "extended_data.connectors entry point group. "
        f'Expected: {name} = "{spec.module_path}:{spec.class_name}"'
    )


def _list_connector_classes() -> dict[str, builtins.type[ConnectorBase]]:
    """List available connector classes for internal tool registration."""
    return _discover_connectors().copy()


def list_connectors() -> ExtendedList[ExtendedString]:
    """List registered connector names whose runtime requirements are installed.

    Returns:
        ExtendedList of usable connector registry names.
    """
    return extend_data(
        sorted(
            name
            for name in _discover_connectors()
            if not get_missing_connector_requirements(name)
        ),
    )


def get_connector_class(name: str) -> builtins.type[ConnectorBase]:
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
        if name_lower in BUILTIN_CONNECTORS:
            _raise_unregistered_builtin_connector(name_lower)
        available = ", ".join(sorted(connectors.keys()))
        raise ValueError(f"Unknown connector: {redact_sensitive_text(name)}. Available: {available}")

    if name_lower in BUILTIN_CONNECTORS:
        missing = get_missing_connector_requirements(name_lower)
        if missing:
            error = ImportError(f"Missing packages: {', '.join(str(package) for package in missing)}")
            _raise_missing_builtin_connector(name_lower, error)

    return connectors[name_lower]


def get_connector(name: str, **kwargs: Any) -> ConnectorBase:
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


def _get_description(cls: builtins.type[ConnectorBase]) -> str | None:
    """Get the first useful line from a connector docstring."""
    if not cls.__doc__:
        return None
    for line in cls.__doc__.splitlines():
        description = line.strip()
        if description:
            return description
    return None


def _get_category(cls: builtins.type[ConnectorBase], spec: BuiltinConnectorSpec | None) -> str:
    """Get normalized category metadata for a connector."""
    raw_category = spec.category if spec else getattr(cls, "CONNECTOR_CATEGORY", "external")
    return _normalize_catalog_token(raw_category) or "external"


def _get_capabilities(cls: builtins.type[ConnectorBase], spec: BuiltinConnectorSpec | None) -> tuple[str, ...]:
    """Get normalized capability metadata for a connector."""
    raw_capabilities = spec.capabilities if spec else getattr(cls, "CONNECTOR_CAPABILITIES", ())
    capability_values = (raw_capabilities,) if isinstance(raw_capabilities, str) else raw_capabilities
    capabilities = [_normalize_catalog_token(capability) for capability in capability_values]
    capabilities = [capability for capability in capabilities if capability]
    return tuple(dict.fromkeys(capabilities))


def _available_connector_info(name: str, cls: builtins.type[ConnectorBase]) -> ConnectorInfo:
    """Build metadata for a loadable connector."""
    spec = BUILTIN_CONNECTORS.get(name)
    source = "builtin" if spec else "entry_point"
    extra_value = spec.extra if spec else get_extra_for_connector(name)
    extra = str(extra_value) if extra_value is not None else None
    requirements = tuple(str(requirement) for requirement in get_connector_requirements(name))
    missing = tuple(str(requirement) for requirement in get_missing_connector_requirements(name))
    install_value = get_connector_install_command(name)

    return ConnectorInfo(
        name=name,
        available=not missing,
        source=source,
        extra=extra,
        category=_get_category(cls, spec),
        capabilities=_get_capabilities(cls, spec),
        install=str(install_value) if install_value is not None else None,
        requirements=requirements,
        missing=missing,
        class_name=cls.__name__,
        module=cls.__module__,
        base_url=getattr(cls, "BASE_URL", None),
        description=_get_description(cls),
        error=None,
    )


def _missing_builtin_connector_info(name: str, error: ImportError | None) -> ConnectorInfo:
    """Build metadata for a known built-in connector that cannot be loaded."""
    spec = BUILTIN_CONNECTORS[name]
    error_message = (
        redact_sensitive_text(error)
        if error
        else "Built-in connector is declared but is not registered in the extended_data.connectors entry point group."
    )

    return ConnectorInfo(
        name=name,
        available=False,
        source="builtin",
        extra=spec.extra,
        category=spec.category,
        capabilities=spec.capabilities,
        install=str(install) if (install := get_connector_install_command(name)) is not None else None,
        requirements=tuple(str(requirement) for requirement in get_connector_requirements(name)),
        missing=tuple(str(requirement) for requirement in get_missing_connector_requirements(name)),
        class_name=spec.class_name,
        module=spec.module_path,
        base_url=None,
        description=None,
        error=error_message,
    )


# =============================================================================
# Connector Info Helpers
# =============================================================================


def get_connector_info(name: str, *, include_unavailable: bool = True) -> ExtendedDict:
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
    raise ValueError(f"Unknown connector: {redact_sensitive_text(name)}. Available: {available}")


def list_connector_info(*, include_unavailable: bool = True) -> ExtendedList[ExtendedDict]:
    """Get registry metadata for known connectors."""
    connectors = _discover_connectors()
    names = set(connectors)
    if include_unavailable:
        names.update(BUILTIN_CONNECTORS)
        names.update(_missing_builtin_connectors)
    info = [get_connector_info(name, include_unavailable=include_unavailable) for name in sorted(names)]
    if not include_unavailable:
        return extend_data([connector for connector in info if connector["available"]])
    return extend_data(info)


def list_connector_categories(*, include_unavailable: bool = True) -> ExtendedList[ExtendedString]:
    """List connector catalog categories."""
    categories = {
        str(connector["category"])
        for connector in list_connector_info(include_unavailable=include_unavailable)
        if connector["category"]
    }
    return extend_data(sorted(categories))


def list_connector_capabilities(*, include_unavailable: bool = True) -> ExtendedList[ExtendedString]:
    """List connector catalog capabilities."""
    capabilities: set[str] = set()
    for connector in list_connector_info(include_unavailable=include_unavailable):
        capabilities.update(str(capability) for capability in connector["capabilities"])
    return extend_data(sorted(capabilities))


def list_connectors_by_category(
    category: str,
    *,
    include_unavailable: bool = True,
) -> ExtendedList[ExtendedDict]:
    """List connector catalog entries for a category."""
    normalized = _normalize_catalog_token(category)
    return extend_data(
        [
            connector
            for connector in list_connector_info(include_unavailable=include_unavailable)
            if str(connector["category"]) == normalized
        ],
    )


def list_connectors_by_capability(
    capability: str,
    *,
    include_unavailable: bool = True,
) -> ExtendedList[ExtendedDict]:
    """List connector catalog entries for a capability."""
    normalized = _normalize_catalog_token(capability)
    return extend_data(
        [
            connector
            for connector in list_connector_info(include_unavailable=include_unavailable)
            if normalized in {str(value) for value in connector["capabilities"]}
        ],
    )
