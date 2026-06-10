"""AI framework tools for Anthropic Claude operations.

This module provides tools for Anthropic operations that work with multiple
AI agent frameworks.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateMessageSchema(BaseModel):
    """Pydantic schema for the anthropic_create_message tool."""

    model: str = Field(..., description="Model ID (e.g., 'claude-sonnet-4-5-20250929')")
    max_tokens: int = Field(1024, description="Maximum tokens to generate")
    prompt: str = Field(..., description="The user prompt text")
    system: str | None = Field(None, description="Optional system prompt")


class ListModelsSchema(BaseModel):
    """Pydantic schema for the anthropic_list_models tool."""


def anthropic_create_message(
    model: str,
    prompt: str,
    max_tokens: int = 1024,
    system: str | None = None,
) -> dict[str, Any]:
    """Create a message using Anthropic Claude.

    Args:
        model: Model ID.
        prompt: User prompt text.
        max_tokens: Max tokens to generate.
        system: Optional system prompt.

    Returns:
        Dict with message ID, text, and usage.
    """
    from extended_data.connectors.anthropic import AnthropicConnector

    connector = AnthropicConnector()
    response = connector.create_message(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
        system=system,
    )

    return {
        "id": response.id,
        "text": response.text,
        "model": response.model,
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
    }


def anthropic_list_models() -> list[dict[str, Any]]:
    """List available Anthropic Claude models.

    Returns:
        List of models with ID and display name.
    """
    from extended_data.connectors.anthropic import AnthropicConnector

    connector = AnthropicConnector()
    models = connector.list_models()

    return [{"id": m.id, "display_name": m.display_name} for m in models]


TOOL_DEFINITIONS = [
    {
        "name": "anthropic_create_message",
        "description": "Create a message using Anthropic Claude AI. Provide a model ID and prompt.",
        "func": anthropic_create_message,
        "schema": CreateMessageSchema,
    },
    {
        "name": "anthropic_list_models",
        "description": "List available Anthropic Claude models.",
        "func": anthropic_list_models,
        "schema": ListModelsSchema,
    },
]


def get_langchain_tools() -> list[Any]:
    """Get all Anthropic tools as LangChain StructuredTools."""
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
    """Get all Anthropic tools as CrewAI tools."""
    try:
        from crewai.tools import tool as crewai_tool
    except ImportError as e:
        msg = "crewai is required for CrewAI tools."
        raise ImportError(msg) from e

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
    """Get all Anthropic tools as plain Python functions for AWS Strands."""
    return [defn["func"] for defn in TOOL_DEFINITIONS]


def get_tools(framework: str = "auto") -> list[Any]:
    """Get Anthropic tools for the specified or auto-detected framework."""
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


__all__ = [
    "TOOL_DEFINITIONS",
    "anthropic_create_message",
    "anthropic_list_models",
    "get_crewai_tools",
    "get_langchain_tools",
    "get_strands_tools",
    "get_tools",
]
