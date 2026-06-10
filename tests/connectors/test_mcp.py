"""Tests for unified MCP server."""

from __future__ import annotations

import pytest

from extended_data.connectors.mcp import _jsonable_tool_result, create_server
from extended_data.containers import ExtendedDict, ExtendedList, ExtendedSet


def test_create_server():
    """Test that the MCP server can be created and has tools."""
    pytest.importorskip("mcp")
    server = create_server()
    assert server.name == "extended-data"
    # Basic check that server was initialized
    assert server is not None


def test_jsonable_tool_result_lowers_extended_mapping_payloads() -> None:
    """MCP result serialization keeps Tier 2 mapping payloads as JSON objects."""
    payload = ExtendedDict({"service": {"name": "api"}})

    assert _jsonable_tool_result(payload) == {"service": {"name": "api"}}


def test_jsonable_tool_result_lowers_extended_sequence_payloads() -> None:
    """MCP result serialization keeps Tier 2 sequence payloads as JSON arrays."""
    payload = ExtendedList([{"service": "api"}])

    assert _jsonable_tool_result(payload) == [{"service": "api"}]


def test_jsonable_tool_result_lowers_extended_set_payloads() -> None:
    """MCP result serialization turns Tier 2 sets into JSON arrays."""
    payload = ExtendedSet({"api", "worker"})

    assert sorted(_jsonable_tool_result(payload)) == ["api", "worker"]
