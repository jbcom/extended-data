"""Tests for unified MCP server."""

from __future__ import annotations

import pytest

from extended_data.connectors.mcp import _get_public_methods, _jsonable_tool_result, _tool_error_text, create_server
from extended_data.connectors.meshy.connector import MeshyConnector
from extended_data.containers import ExtendedDict, ExtendedList, ExtendedSet


def test_create_server() -> None:
    """Test that the MCP server can be created and has tools."""
    pytest.importorskip("mcp")
    server = create_server()
    assert server.name == "extended-data"
    # Basic check that server was initialized
    assert server is not None


def test_mcp_public_methods_only_include_extended_payload_boundaries() -> None:
    """Generic MCP exposure should skip raw clients and inherited base helpers."""
    method_names = {name for name, _ in _get_public_methods(MeshyConnector)}

    assert "text3d_generate" in method_names
    assert "image3d_generate" in method_names
    assert "request_data" not in method_names
    assert "decode_response" not in method_names
    assert "get_ai_tool_definitions" not in method_names
    assert "freeze_inputs" not in method_names
    assert "merge_inputs" not in method_names
    assert "replace_inputs" not in method_names


def test_jsonable_tool_result_lowers_extended_mapping_payloads() -> None:
    """MCP result serialization keeps Tier 2 mapping payloads as JSON objects."""
    payload = ExtendedDict({"service": {"name": "api"}})

    assert _jsonable_tool_result(payload) == {"service": {"name": "api"}}


def test_jsonable_tool_result_redacts_sensitive_mapping_payloads() -> None:
    """MCP result serialization should not bypass connector redaction."""
    payload = ExtendedDict({"password": "hunter2", "nested": {"api_key": "key_123"}})

    assert _jsonable_tool_result(payload) == {"password": "[REDACTED]", "nested": {"api_key": "[REDACTED]"}}


def test_jsonable_tool_result_lowers_extended_sequence_payloads() -> None:
    """MCP result serialization keeps Tier 2 sequence payloads as JSON arrays."""
    payload = ExtendedList([{"service": "api"}])

    assert _jsonable_tool_result(payload) == [{"service": "api"}]


def test_jsonable_tool_result_redacts_sensitive_sequence_payloads() -> None:
    """MCP result serialization should redact secrets inside array payloads."""
    payload = ExtendedList([{"name": "api", "access_token": "tok_123"}, {"message": "client_secret=raw"}])

    assert _jsonable_tool_result(payload) == [
        {"name": "api", "access_token": "[REDACTED]"},
        {"message": "client_secret=[REDACTED]"},
    ]


def test_jsonable_tool_result_lowers_extended_set_payloads() -> None:
    """MCP result serialization turns Tier 2 sets into JSON arrays."""
    payload = ExtendedSet({"api", "worker"})

    assert sorted(_jsonable_tool_result(payload)) == ["api", "worker"]


def test_tool_error_text_redacts_sensitive_exception_values() -> None:
    """Generic MCP errors should not bypass connector redaction."""
    error = RuntimeError("failed password=hunter2 Authorization: Bearer raw_token")

    text = _tool_error_text(error)

    assert "hunter2" not in text
    assert "raw_token" not in text
    assert "[REDACTED]" in text
