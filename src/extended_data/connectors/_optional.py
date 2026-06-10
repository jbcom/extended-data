"""Optional dependency utilities.

This module provides utilities for checking optional dependencies and
providing helpful error messages when they're missing.

Usage:
    from extended_data.connectors._optional import require_extra, is_available

    # Check if available (returns bool)
    if is_available("boto3"):
        import boto3

    # Require with helpful error (raises ImportError)
    require_extra("boto3", "aws")  # -> "Install with: pip install extended-data[aws]"
"""

from __future__ import annotations

import importlib

from typing import Any


# Mapping of package names to their extras
PACKAGE_TO_EXTRA: dict[str, str] = {
    # Vendor connectors
    "boto3": "aws",
    "google.cloud": "google",
    "google.api_core": "google",
    "googleapiclient": "google",
    "github": "github",
    "python_graphql_client": "github",
    "slack_sdk": "slack",
    "hvac": "vault",
    "anthropic": "anthropic",
    "rich": "meshy",
    "numpy": "meshy",
    "validators": "meshy",
    # AI frameworks
    "langchain_core": "langchain",
    "langchain": "langchain",
    "crewai": "crewai",
    "strands": "strands",
    "mcp": "mcp",
    # Features
    "fastapi": "webhooks",
    "uvicorn": "webhooks",
    "sqlite_vec": "vector",
    "sentence_transformers": "vector",
}

# Cache for import checks
_import_cache: dict[str, bool] = {}


def is_available(package: str) -> bool:
    """Check if a package is available for import.

    Args:
        package: Package name to check (e.g., "boto3", "langchain_core")

    Returns:
        True if package can be imported, False otherwise
    """
    if package in _import_cache:
        return _import_cache[package]

    try:
        importlib.import_module(package)
        _import_cache[package] = True
        return True
    except ImportError:
        _import_cache[package] = False
        return False


def get_extra_for_package(package: str) -> str | None:
    """Get the extra name for a package.

    Args:
        package: Package name

    Returns:
        Extra name or None if not mapped
    """
    return PACKAGE_TO_EXTRA.get(package)


def require_extra(package: str, extra: str | None = None) -> Any:
    """Import a package, raising helpful error if missing.

    Args:
        package: Package name to import
        extra: Optional extra name override (auto-detected if not provided)

    Returns:
        The imported module

    Raises:
        ImportError: With helpful install instructions if package is missing
    """
    try:
        return importlib.import_module(package)
    except ImportError as e:
        extra_name = extra or get_extra_for_package(package) or package
        raise ImportError(
            f"Package '{package}' is required but not installed.\n"
            f"Install with: pip install extended-data[{extra_name}]"
        ) from e


def require_any(*packages: str, extra: str) -> Any:
    """Import the first available package from a list.

    Args:
        *packages: Package names to try (in order)
        extra: Extra name for error message

    Returns:
        The first successfully imported module

    Raises:
        ImportError: If none of the packages are available
    """
    errors = []
    for package in packages:
        try:
            return importlib.import_module(package)
        except ImportError as e:
            errors.append(str(e))

    raise ImportError(
        f"None of the required packages are installed: {', '.join(packages)}\n"
        f"Install with: pip install extended-data[{extra}]"
    )


# === Framework Detection ===


def detect_ai_frameworks() -> dict[str, bool]:
    """Detect which AI frameworks are available.

    Returns:
        Dict mapping framework name to availability
    """
    return {
        "langchain": is_available("langchain_core"),
        "crewai": is_available("crewai"),
        "strands": is_available("strands"),
        "mcp": is_available("mcp"),
    }


def get_available_ai_frameworks() -> list[str]:
    """Get list of available AI frameworks.

    Returns:
        List of framework names that are installed
    """
    return [name for name, available in detect_ai_frameworks().items() if available]


# === Connector Availability ===

CONNECTOR_REQUIREMENTS: dict[str, list[str]] = {
    # Core-only connectors (always available)
    "meshy": [],  # httpx, pydantic, tenacity are in core
    "zoom": [],  # requests is in core
    "cursor": [],  # httpx is in core
    # Connectors requiring extras
    "aws": ["boto3"],
    "google": ["googleapiclient"],
    "github": ["github"],
    "slack": ["slack_sdk"],
    "vault": ["hvac"],
    "anthropic": ["anthropic"],
}


def is_connector_available(connector: str) -> bool:
    """Check if a connector's dependencies are available.

    Args:
        connector: Connector name (e.g., "aws", "meshy")

    Returns:
        True if all required packages are available
    """
    requirements = CONNECTOR_REQUIREMENTS.get(connector, [])
    return all(is_available(pkg) for pkg in requirements)


def get_available_connectors() -> list[str]:
    """Get list of connectors with available dependencies.

    Returns:
        List of connector names that can be used
    """
    return [name for name in CONNECTOR_REQUIREMENTS if is_connector_available(name)]


def require_connector(connector: str) -> None:
    """Ensure a connector's dependencies are available.

    Args:
        connector: Connector name

    Raises:
        ImportError: With helpful message if dependencies missing
    """
    requirements = CONNECTOR_REQUIREMENTS.get(connector, [])
    missing = [pkg for pkg in requirements if not is_available(pkg)]

    if missing:
        raise ImportError(
            f"The '{connector}' connector requires additional dependencies.\n"
            f"Missing packages: {', '.join(missing)}\n"
            f"Install with: pip install extended-data[{connector}]"
        )
