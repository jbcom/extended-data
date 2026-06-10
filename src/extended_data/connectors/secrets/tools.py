"""AI framework tools for secrets synchronization operations.

This module provides tools for secrets sync operations that work with
multiple AI agent frameworks including LangChain, CrewAI, and AWS Strands.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from pydantic import BaseModel, Field

from extended_data.connectors.redaction import redact_sensitive_data
from extended_data.containers import ExtendedDict, extend_data


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
        True,
        description="Continue processing remaining targets after an error",
    )


class GetConfigInfoSchema(BaseModel):
    """Schema for getting configuration information."""

    config_path: str = Field(..., description="Path to the YAML configuration file")


# =============================================================================
# Tool Implementation Functions
# =============================================================================


def _redacted_extended_payload(value: Any) -> ExtendedDict:
    """Promote a connector payload after redacting terminal-sensitive fields."""
    return cast(ExtendedDict, extend_data(redact_sensitive_data(value)))


def _redacted_mapping(value: Any) -> Mapping[str, Any]:
    """Return a redacted mapping view for tool payload summaries."""
    redacted = redact_sensitive_data(value)
    if isinstance(redacted, Mapping):
        return redacted
    return {}


def validate_config(config_path: str) -> ExtendedDict:
    """Validate a secrets sync pipeline configuration file.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Dict with 'valid' (bool) and 'message' (str) fields
    """
    from extended_data.connectors.secrets import SecretsConnector

    connector = SecretsConnector()
    return _redacted_extended_payload(connector.validate_config(config_path))


def run_pipeline(
    config_path: str,
    dry_run: bool = False,
    operation: str = "pipeline",
    targets: str | None = None,
    continue_on_error: bool = True,
) -> ExtendedDict:
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

    result = _redacted_mapping(connector.run_pipeline(config_path, options))

    return _redacted_extended_payload({
        "success": result.get("success", False),
        "target_count": result.get("target_count", 0),
        "secrets_processed": result.get("secrets_processed", 0),
        "secrets_added": result.get("secrets_added", 0),
        "secrets_modified": result.get("secrets_modified", 0),
        "secrets_removed": result.get("secrets_removed", 0),
        "secrets_unchanged": result.get("secrets_unchanged", 0),
        "duration_ms": result.get("duration_ms", 0),
        "error_message": result.get("error_message", ""),
        "diff_output": result.get("diff_output", "") if dry_run else "",
    })


def dry_run(config_path: str) -> ExtendedDict:
    """Perform a dry run to see what changes would be made.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Dict with what would be changed, including diff output
    """
    from extended_data.connectors.secrets import SecretsConnector

    connector = SecretsConnector()
    result = _redacted_mapping(connector.dry_run(config_path))

    return _redacted_extended_payload({
        "success": result.get("success", False),
        "target_count": result.get("target_count", 0),
        "secrets_would_add": result.get("secrets_added", 0),
        "secrets_would_modify": result.get("secrets_modified", 0),
        "secrets_would_remove": result.get("secrets_removed", 0),
        "secrets_unchanged": result.get("secrets_unchanged", 0),
        "diff_output": result.get("diff_output", ""),
        "error_message": result.get("error_message", ""),
    })


def get_config_info(config_path: str) -> ExtendedDict:
    """Get detailed information about a pipeline configuration.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Dict with configuration details including sources and targets
    """
    from extended_data.connectors.secrets import SecretsConnector

    connector = SecretsConnector()
    return _redacted_extended_payload(connector.get_config_info(config_path))


def get_targets(config_path: str) -> ExtendedDict:
    """Get the list of sync targets from a configuration.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Dict with 'targets' list and any error message
    """
    from extended_data.connectors.secrets import SecretsConnector

    connector = SecretsConnector()
    return _redacted_extended_payload(connector.get_targets(config_path))


def get_sources(config_path: str) -> ExtendedDict:
    """Get the list of secret sources from a configuration.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Dict with 'sources' list and any error message
    """
    from extended_data.connectors.secrets import SecretsConnector

    connector = SecretsConnector()
    return _redacted_extended_payload(connector.get_sources(config_path))


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
    from extended_data.connectors.ai_tools import build_langchain_tools

    return build_langchain_tools(TOOL_DEFINITIONS)


def get_crewai_tools() -> list[Any]:
    """Get all secrets sync tools as CrewAI tools."""
    from extended_data.connectors._optional import get_crewai_tool_decorator

    crewai_tool = get_crewai_tool_decorator()

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
        framework: One of 'auto', 'langchain', 'crewai', 'strands'

    Returns:
        List of tools in the appropriate format
    """
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
    if framework == "strands":
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
