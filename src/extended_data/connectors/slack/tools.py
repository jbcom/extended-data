"""AI framework tools for Slack operations.

This module provides tools for Slack operations that work with multiple
AI agent frameworks. The core functions are framework-agnostic Python functions,
with native wrappers for each supported framework.

Supported Frameworks:
- LangChain (via langchain-core) - get_langchain_tools()
- CrewAI - get_crewai_tools()
- AWS Strands - get_strands_tools() (plain functions)
- Auto-detection - get_tools() picks the best available

Tools provided:
- slack_list_channels: List Slack channels
- slack_list_users: List Slack users
- slack_send_message: Send a message to a channel
- slack_get_channel_history: Get recent messages from a channel

Usage:
    from extended_data.connectors.slack.tools import get_tools
    tools = get_tools()  # Returns best format for installed framework
"""

from __future__ import annotations

import os

from typing import Any

from pydantic import BaseModel, Field


# =============================================================================
# Input Schemas
# =============================================================================


class ListChannelsSchema(BaseModel):
    """Schema for listing Slack channels."""

    exclude_archived: bool = Field(True, description="Exclude archived channels when True.")
    channels_only: bool = Field(True, description="Return only channel-type conversations when True.")
    limit: int = Field(100, description="Maximum number of channels to return.")


class ListUsersSchema(BaseModel):
    """Schema for listing Slack users."""

    include_bots: bool = Field(False, description="Include bot accounts when True.")
    include_deleted: bool = Field(False, description="Include deactivated accounts when True.")
    max_results: int = Field(100, description="Maximum number of users to return.")


class SendMessageSchema(BaseModel):
    """Schema for sending a Slack message."""

    channel: str = Field(..., description="Channel name (without #) to send message to.")
    text: str = Field(..., description="Message text to send.")
    thread_id: str = Field("", description="Optional thread timestamp to reply in a thread.")


class GetChannelHistorySchema(BaseModel):
    """Schema for getting Slack channel history."""

    channel: str = Field(..., description="Channel name (without #) to get history from.")
    limit: int = Field(100, description="Maximum number of messages to return.")


# =============================================================================
# Helper Functions
# =============================================================================


def _get_connector():
    """Create a SlackConnector with tokens from environment variables.

    The slack_sdk WebClient only falls back to environment variables when
    token=None, not when given empty strings. We explicitly load tokens
    from environment to ensure proper authentication.

    Returns:
        SlackConnector: Configured Slack connector instance.
    """
    from extended_data.connectors.slack import SlackConnector

    return SlackConnector(
        token=os.environ.get("SLACK_TOKEN"),
        bot_token=os.environ.get("SLACK_BOT_TOKEN"),
    )


# =============================================================================
# Tool Implementation Functions
# =============================================================================


def list_channels(
    exclude_archived: bool = True,
    channels_only: bool = True,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List Slack channels.

    Args:
        exclude_archived: Exclude archived channels when True
        channels_only: Return only channel-type conversations when True
        limit: Maximum number of channels to return

    Returns:
        List of channels with their properties (id, name, is_private, topic, purpose, member_count)
    """
    connector = _get_connector()
    channels = connector.list_conversations(
        exclude_archived=exclude_archived,
        channels_only=channels_only,
        limit=limit,
    )

    result = []
    for channel_id, data in list(channels.items())[:limit]:
        result.append(
            {
                "id": channel_id,
                "name": data.get("name", ""),
                "is_private": data.get("is_private", False),
                "topic": data.get("topic", {}).get("value", "") if isinstance(data.get("topic"), dict) else "",
                "purpose": data.get("purpose", {}).get("value", "") if isinstance(data.get("purpose"), dict) else "",
                "member_count": data.get("num_members", 0),
            }
        )

    return result


def list_users(
    include_bots: bool = False,
    include_deleted: bool = False,
    max_results: int = 100,
) -> list[dict[str, Any]]:
    """List Slack users.

    Args:
        include_bots: Include bot accounts when True
        include_deleted: Include deactivated accounts when True
        max_results: Maximum number of users to return

    Returns:
        List of users with their properties (id, name, real_name, email, is_admin, is_bot)
    """
    connector = _get_connector()
    users = connector.list_users(
        include_bots=include_bots,
        include_deleted=include_deleted,
        limit=max_results,
    )

    result = []
    for user_id, data in list(users.items())[:max_results]:
        profile = data.get("profile", {})
        result.append(
            {
                "id": user_id,
                "name": data.get("name", ""),
                "real_name": data.get("real_name", ""),
                "email": profile.get("email", "") if isinstance(profile, dict) else "",
                "is_admin": data.get("is_admin", False),
                "is_bot": data.get("is_bot", False),
            }
        )

    return result


def send_message(
    channel: str,
    text: str,
    thread_id: str = "",
) -> dict[str, Any]:
    """Send a message to a Slack channel.

    Args:
        channel: Channel name (without #) to send message to
        text: Message text to send
        thread_id: Optional thread timestamp to reply in a thread

    Returns:
        Dict with channel, text, and timestamp of the sent message
    """
    connector = _get_connector()
    timestamp = connector.send_message(
        channel_name=channel,
        text=text,
        thread_id=thread_id or None,
    )

    return {
        "channel": channel,
        "text": text,
        "timestamp": timestamp,
        "status": "sent",
    }


def get_channel_history(
    channel: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Get recent messages from a Slack channel.

    Args:
        channel: Channel name (without #) to get history from
        limit: Maximum number of messages to return

    Returns:
        List of messages with their properties (timestamp, user, text, type)
    """
    connector = _get_connector()

    # Get channel ID from name
    channels = connector.list_conversations()
    channel_id = None
    for cid, cdata in channels.items():
        if cdata.get("name") == channel:
            channel_id = cid
            break

    if not channel_id:
        return []

    # Get conversation history using the internal _call_api method
    history = connector._call_api(
        "conversations_history",
        channel=channel_id,
        limit=limit,
    )

    # Extract messages
    messages = history.get("messages", []) if isinstance(history, dict) else []

    result = []
    for msg in messages:
        result.append(
            {
                "timestamp": msg.get("ts", ""),
                "user": msg.get("user", msg.get("bot_id", "")),
                "text": msg.get("text", ""),
                "type": msg.get("type", "message"),
            }
        )

    return result


# =============================================================================
# Tool Definitions
# =============================================================================

TOOL_DEFINITIONS = [
    {
        "name": "slack_list_channels",
        "description": "List Slack channels with their properties. Returns channel names, IDs, topics, and member counts.",
        "func": list_channels,
        "schema": ListChannelsSchema,
    },
    {
        "name": "slack_list_users",
        "description": "List Slack users with their profiles. Returns user names, emails, and roles.",
        "func": list_users,
        "schema": ListUsersSchema,
    },
    {
        "name": "slack_send_message",
        "description": "Send a message to a Slack channel. Can optionally reply in a thread.",
        "func": send_message,
        "schema": SendMessageSchema,
    },
    {
        "name": "slack_get_channel_history",
        "description": "Get recent messages from a Slack channel. Returns message history with timestamps and users.",
        "func": get_channel_history,
        "schema": GetChannelHistorySchema,
    },
]


# =============================================================================
# Framework-Specific Getters
# =============================================================================


def get_langchain_tools() -> list[Any]:
    """Get all Slack tools as LangChain StructuredTools.

    Returns:
        List of LangChain StructuredTool objects.

    Raises:
        ImportError: If langchain-core is not installed.
    """
    try:
        from langchain_core.tools import StructuredTool
    except ImportError as e:
        msg = "langchain-core is required for LangChain tools.\nInstall with: pip install extended-data[langchain]"
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
    """Get all Slack tools as CrewAI tools.

    Returns:
        List of CrewAI BaseTool objects.

    Raises:
        ImportError: If crewai is not installed.
    """
    try:
        from crewai.tools import tool as crewai_tool
    except ImportError as e:
        msg = "crewai is required for CrewAI tools.\nInstall with: pip install extended-data[crewai]"
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
    """Get all Slack tools as plain Python functions for AWS Strands.

    Returns:
        List of callable functions.
    """
    return [defn["func"] for defn in TOOL_DEFINITIONS]


def get_tools(framework: str = "auto") -> list[Any]:
    """Get Slack tools for the specified or auto-detected framework.

    Args:
        framework: Framework to use. Options:
            - "auto" (default): Auto-detect based on installed packages
            - "langchain": Force LangChain StructuredTools
            - "crewai": Force CrewAI tools
            - "strands": Force plain functions for Strands
            - "functions": Force plain functions (alias for strands)

    Returns:
        List of tools in the appropriate format for the framework.

    Raises:
        ImportError: If the requested framework is not installed.
        ValueError: If an unknown framework is specified.
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
    if framework in ("strands", "functions"):
        return get_strands_tools()

    raise ValueError(f"Unknown framework: {framework}. Options: auto, langchain, crewai, strands, functions")


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Tool metadata
    "TOOL_DEFINITIONS",
    "get_channel_history",
    "get_crewai_tools",
    "get_langchain_tools",
    "get_strands_tools",
    # Framework-specific getters
    "get_tools",
    # Raw functions
    "list_channels",
    "list_users",
    "send_message",
]
