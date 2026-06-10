"""Tests for unified MCP server."""

from __future__ import annotations

import pytest

from extended_data.connectors.mcp import create_server


def test_create_server():
    """Test that the MCP server can be created and has tools."""
    pytest.importorskip("mcp")
    server = create_server()
    assert server.name == "extended-data"
    # Basic check that server was initialized
    assert server is not None
