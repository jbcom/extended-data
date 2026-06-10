"""Tests for Cursor AI tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from extended_data.connectors.cursor import AgentState
from extended_data.containers import ExtendedDict, ExtendedString


def test_cursor_launch_agent():
    """Test launch_agent tool."""
    from extended_data.connectors.cursor.tools import cursor_launch_agent

    with patch("extended_data.connectors.cursor.CursorConnector") as mock_connector_class:
        mock_connector = MagicMock()
        mock_agent = MagicMock()
        mock_agent.id = "agent_123"
        mock_agent.state = AgentState.RUNNING
        mock_agent.repository = "org/repo"
        mock_connector.launch_agent.return_value = mock_agent
        mock_connector_class.return_value = mock_connector

        result = cursor_launch_agent(prompt="Fix bug", repository="org/repo")
        assert isinstance(result, ExtendedDict)
        assert isinstance(result["agent_id"], ExtendedString)
        assert result["agent_id"] == "agent_123"
        assert result["state"] == "running"
        assert result["repository"].sanitize() == "org_repo"


def test_cursor_get_agent_status():
    """Test get_agent_status tool."""
    from extended_data.connectors.cursor.tools import cursor_get_agent_status

    with patch("extended_data.connectors.cursor.CursorConnector") as mock_connector_class:
        mock_connector = MagicMock()
        mock_agent = MagicMock()
        mock_agent.id = "agent_123"
        mock_agent.state = AgentState.FINISHED
        mock_agent.error = None
        mock_agent.pr_url = "https://github.com/org/repo/pull/1"
        mock_connector.get_agent_status.return_value = mock_agent
        mock_connector_class.return_value = mock_connector

        result = cursor_get_agent_status(agent_id="agent_123")
        assert isinstance(result, ExtendedDict)
        assert isinstance(result["state"], ExtendedString)
        assert result["agent_id"] == "agent_123"
        assert result["state"] == "finished"
        assert result["pr_url"] == "https://github.com/org/repo/pull/1"
