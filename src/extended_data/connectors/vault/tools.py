"""AI framework tools for HashiCorp Vault operations.

This module provides tools for Vault operations that work with multiple
AI agent frameworks.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, Field

from extended_data.containers import ExtendedDict, ExtendedList, extend_data


# =============================================================================
# Input Schemas
# =============================================================================


class ListSecretsSchema(BaseModel):
    """Schema for listing Vault secrets."""

    root_path: str = Field("/", description="Root path to search (e.g., '/').")
    mount_point: str = Field("secret", description="KV engine mount point.")
    max_depth: int | None = Field(None, description="Maximum directory depth to traverse.")


class ReadSecretSchema(BaseModel):
    """Schema for reading a Vault secret."""

    path: str = Field(..., description="Path to the secret.")
    mount_point: str = Field("secret", description="KV engine mount point.")


# =============================================================================
# Tool Implementation Functions
# =============================================================================


def list_secrets(
    root_path: str = "/",
    mount_point: str = "secret",
    max_depth: int | None = 10,
) -> ExtendedList[ExtendedDict]:
    """List secrets recursively from Vault KV v2 engine.

    Args:
        root_path: Root path to search.
        mount_point: KV engine mount point.
        max_depth: Max traversal depth.

    Returns:
        List of secret data dicts with path, mount_point, data, and key_count.
    """
    from extended_data.connectors.vault import VaultConnector

    connector = VaultConnector()
    secrets = connector.list_secrets(root_path=root_path, mount_point=mount_point, max_depth=max_depth)

    result = []
    for path, data in secrets.items():
        result.append(
            {
                "path": path,
                "mount_point": mount_point,
                "data": data,
                "key_count": len(data) if isinstance(data, Mapping) else 0,
            }
        )
    return extend_data(result)


def read_secret(
    path: str,
    mount_point: str = "secret",
) -> ExtendedDict:
    """Read a single secret from Vault.

    Args:
        path: Path to the secret.
        mount_point: KV engine mount point.

    Returns:
        Dict with path, mount_point, data, and found status.
    """
    from extended_data.connectors.vault import VaultConnector

    connector = VaultConnector()
    data = connector.read_secret(path=path, mount_point=mount_point)

    return extend_data(
        {
            "path": path,
            "mount_point": mount_point,
            "data": data or {},
            "found": data is not None,
        }
    )


# =============================================================================
# Tool Definitions
# =============================================================================

TOOL_DEFINITIONS = [
    {
        "name": "vault_list_secrets",
        "description": "Recursively list all secrets and their values under a specific Vault path.",
        "func": list_secrets,
        "schema": ListSecretsSchema,
    },
    {
        "name": "vault_read_secret",
        "description": "Retrieve the data for a specific HashiCorp Vault secret by its path.",
        "func": read_secret,
        "schema": ReadSecretSchema,
    },
]


# =============================================================================
# Framework-Specific Getters
# =============================================================================


def get_langchain_tools() -> list[Any]:
    """Get all Vault tools as LangChain StructuredTools."""
    try:
        from langchain_core.tools import StructuredTool
    except ImportError as e:
        msg = "langchain-core is required for LangChain tools."
        raise ImportError(msg) from e

    return [
        StructuredTool.from_function(
            func=defn["func"],
            name=defn["name"],
            description=defn["description"],
            args_schema=defn.get("schema") or defn.get("args_schema"),
        )
        for defn in TOOL_DEFINITIONS
    ]


def get_crewai_tools() -> list[Any]:
    """Get all Vault tools as CrewAI tools."""
    from extended_data.connectors._optional import get_crewai_tool_decorator

    crewai_tool = get_crewai_tool_decorator()

    tools = []
    for defn in TOOL_DEFINITIONS:
        wrapped = crewai_tool(defn["name"])(defn["func"])
        wrapped.description = defn["description"]
        schema = defn.get("schema") or defn.get("args_schema")
        if schema:
            wrapped.args_schema = schema
        tools.append(wrapped)

    return tools


def get_strands_tools() -> list[Any]:
    """Get all Vault tools as plain Python functions for AWS Strands."""
    return [defn["func"] for defn in TOOL_DEFINITIONS]


def get_tools(framework: str = "auto") -> list[Any]:
    """Get Vault tools for the specified or auto-detected framework."""
    from extended_data.connectors._optional import is_available

    if framework == "auto":
        if is_available("crewai"):
            return get_crewai_tools()
        if is_available("langchain_core"):
            return get_langchain_tools()
        return get_strands_tools()

    if framework == "langchain":
        return get_langchain_tools()
    if framework == "crewai":
        return get_crewai_tools()
    if framework in ("strands", "functions"):
        return get_strands_tools()

    raise ValueError(f"Unknown framework: {framework}")


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "TOOL_DEFINITIONS",
    "get_crewai_tools",
    "get_langchain_tools",
    "get_strands_tools",
    "get_tools",
    "list_secrets",
    "read_secret",
]
