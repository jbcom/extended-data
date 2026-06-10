"""AI framework tools for secrets synchronization operations.

This module provides tools for secrets sync operations that work with
multiple AI agent frameworks including LangChain, CrewAI, and AWS Strands.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# =============================================================================
# Input Schemas
# =============================================================================


class ValidateConfigSchema(BaseModel):
    """Schema for validating a secrets sync configuration."""

    config_path: str = Field(..., description="Path to the YAML configuration file")


class RunPipelineSchema(BaseModel):
    """Schema for running the secrets sync pipeline."""

    config_path: str = Field(..., description="Path to the YAML configuration file")
    dry_run: bool = Field(False, description="If true, don't make actual changes")
    operation: str = Field(
        "pipeline",
        description="Operation type: 'merge', 'sync', or 'pipeline' (full)",
    )
    targets: str | None = Field(
        None,
        description="Comma-separated list of targets to sync (empty for all)",
    )
    continue_on_error: bool = Field(
        False,
        description="Continue processing if errors occur",
    )


class GetConfigInfoSchema(BaseModel):
    """Schema for getting configuration information."""

    config_path: str = Field(..., description="Path to the YAML configuration file")


# =============================================================================
# Tool Implementation Functions
# =============================================================================


def validate_config(config_path: str) -> dict[str, Any]:
    """Validate a secrets sync pipeline configuration file.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Dict with 'valid' (bool) and 'message' (str) fields
    """
    from extended_data.connectors.secrets import SecretsConnector

    connector = SecretsConnector()
    is_valid, message = connector.validate_config(config_path)

    return {
        "valid": is_valid,
        "message": message,
        "config_path": config_path,
    }


def run_pipeline(
    config_path: str,
    dry_run: bool = False,
    operation: str = "pipeline",
    targets: str | None = None,
    continue_on_error: bool = False,
) -> dict[str, Any]:
    """Run the secrets synchronization pipeline.

    This executes the two-phase pipeline (merge → sync) to synchronize
    secrets from HashiCorp Vault to AWS Secrets Manager.

    Args:
        config_path: Path to the YAML configuration file
        dry_run: If true, compute diff but don't make changes
        operation: 'merge', 'sync', or 'pipeline' (full)
        targets: Comma-separated list of targets (empty for all)
        continue_on_error: Continue if errors occur

    Returns:
        Dict with sync results including success, counts, and any errors
    """
    from extended_data.connectors.secrets import (
        SecretsConnector,
        SyncOperation,
        SyncOptions,
    )

    connector = SecretsConnector()

    # Parse operation
    op_map = {
        "merge": SyncOperation.MERGE,
        "sync": SyncOperation.SYNC,
        "pipeline": SyncOperation.PIPELINE,
    }
    sync_operation = op_map.get(operation, SyncOperation.PIPELINE)

    # Parse targets
    target_list = []
    if targets:
        target_list = [t.strip() for t in targets.split(",") if t.strip()]

    options = SyncOptions(
        dry_run=dry_run,
        operation=sync_operation,
        targets=target_list,
        continue_on_error=continue_on_error,
        compute_diff=dry_run,
    )

    result = connector.run_pipeline(config_path, options)

    return {
        "success": result.success,
        "target_count": result.target_count,
        "secrets_processed": result.secrets_processed,
        "secrets_added": result.secrets_added,
        "secrets_modified": result.secrets_modified,
        "secrets_removed": result.secrets_removed,
        "secrets_unchanged": result.secrets_unchanged,
        "duration_ms": result.duration_ms,
        "error_message": result.error_message,
        "diff_output": result.diff_output if dry_run else "",
    }


def dry_run(config_path: str) -> dict[str, Any]:
    """Perform a dry run to see what changes would be made.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Dict with what would be changed, including diff output
    """
    from extended_data.connectors.secrets import SecretsConnector

    connector = SecretsConnector()
    result = connector.dry_run(config_path)

    return {
        "success": result.success,
        "target_count": result.target_count,
        "secrets_would_add": result.secrets_added,
        "secrets_would_modify": result.secrets_modified,
        "secrets_would_remove": result.secrets_removed,
        "secrets_unchanged": result.secrets_unchanged,
        "diff_output": result.diff_output,
        "error_message": result.error_message,
    }


def get_config_info(config_path: str) -> dict[str, Any]:
    """Get detailed information about a pipeline configuration.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Dict with configuration details including sources and targets
    """
    from extended_data.connectors.secrets import SecretsConnector

    connector = SecretsConnector()
    info = connector.get_config_info(config_path)

    return {
        "valid": info.valid,
        "error_message": info.error_message,
        "source_count": info.source_count,
        "target_count": info.target_count,
        "sources": info.sources,
        "targets": info.targets,
        "has_merge_store": info.has_merge_store,
        "vault_address": info.vault_address,
        "aws_region": info.aws_region,
    }


def get_targets(config_path: str) -> dict[str, Any]:
    """Get the list of sync targets from a configuration.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Dict with 'targets' list and any error message
    """
    from extended_data.connectors.secrets import SecretsConnector

    connector = SecretsConnector()
    targets, error = connector.get_targets(config_path)

    return {
        "targets": targets,
        "count": len(targets),
        "error_message": error,
    }


def get_sources(config_path: str) -> dict[str, Any]:
    """Get the list of secret sources from a configuration.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Dict with 'sources' list and any error message
    """
    from extended_data.connectors.secrets import SecretsConnector

    connector = SecretsConnector()
    sources, error = connector.get_sources(config_path)

    return {
        "sources": sources,
        "count": len(sources),
        "error_message": error,
    }


# =============================================================================
# Tool Definitions
# =============================================================================

TOOL_DEFINITIONS = [
    {
        "name": "secrets_validate_config",
        "description": "Validate a secrets sync pipeline configuration file for correctness",
        "func": validate_config,
        "schema": ValidateConfigSchema,
    },
    {
        "name": "secrets_run_pipeline",
        "description": "Execute the secrets synchronization pipeline to sync secrets from Vault to AWS",
        "func": run_pipeline,
        "schema": RunPipelineSchema,
    },
    {
        "name": "secrets_dry_run",
        "description": "Perform a dry run to preview what changes would be made without executing them",
        "func": dry_run,
        "schema": ValidateConfigSchema,
    },
    {
        "name": "secrets_get_config_info",
        "description": "Get detailed information about a secrets sync configuration including sources and targets",
        "func": get_config_info,
        "schema": GetConfigInfoSchema,
    },
    {
        "name": "secrets_get_targets",
        "description": "Get the list of sync targets (AWS accounts/destinations) from a configuration",
        "func": get_targets,
        "schema": ValidateConfigSchema,
    },
    {
        "name": "secrets_get_sources",
        "description": "Get the list of secret sources (Vault paths) from a configuration",
        "func": get_sources,
        "schema": ValidateConfigSchema,
    },
]


# =============================================================================
# Framework-Specific Getters
# =============================================================================


def get_langchain_tools() -> list[Any]:
    """Get all secrets sync tools as LangChain StructuredTools."""
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
            args_schema=defn.get("schema"),
        )
        for defn in TOOL_DEFINITIONS
    ]


def get_crewai_tools() -> list[Any]:
    """Get all secrets sync tools as CrewAI tools."""
    try:
        from crewai.tools import tool as crewai_tool
    except ImportError as e:
        msg = "crewai is required for CrewAI tools."
        raise ImportError(msg) from e

    tools = []
    for defn in TOOL_DEFINITIONS:
        wrapped = crewai_tool(defn["name"])(defn["func"])
        wrapped.description = defn["description"]
        schema = defn.get("schema")
        if schema:
            wrapped.args_schema = schema
        tools.append(wrapped)

    return tools


def get_strands_tools() -> list[Any]:
    """Get all secrets sync tools as plain Python functions for AWS Strands."""
    return [defn["func"] for defn in TOOL_DEFINITIONS]


def get_tools(framework: str = "auto") -> list[Any]:
    """Get secrets sync tools for the specified or auto-detected framework.

    Args:
        framework: One of 'auto', 'langchain', 'crewai', 'strands', 'functions'

    Returns:
        List of tools in the appropriate format
    """
    from extended_data.connectors._compat import is_available

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
    "dry_run",
    "get_config_info",
    "get_crewai_tools",
    "get_langchain_tools",
    "get_sources",
    "get_strands_tools",
    "get_targets",
    "get_tools",
    "run_pipeline",
    "validate_config",
]
