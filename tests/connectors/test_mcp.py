"""Tests for unified MCP server."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from extended_data.connectors import mcp as mcp_module
from extended_data.connectors.mcp import (
    _catalog_tool_definitions,
    _get_public_methods,
    _jsonable_tool_result,
    _tool_error_text,
    _tool_result_text,
    _unknown_tool_text,
    create_server,
)
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


def test_catalog_tools_expose_connector_discovery_without_credentials() -> None:
    """Generic MCP should expose connector catalog queries as first-class tools."""
    tools = _catalog_tool_definitions()

    expected = {
        "extended_data_list_connectors",
        "extended_data_list_available_connectors",
        "extended_data_list_connector_info",
        "extended_data_get_connector_info",
        "extended_data_list_connector_categories",
        "extended_data_list_connector_capabilities",
        "extended_data_list_connectors_by_category",
        "extended_data_list_connectors_by_capability",
    }

    assert expected <= set(tools)
    assert tools["extended_data_get_connector_info"]["parameters"]["required"] == ["name"]
    assert tools["extended_data_list_connectors_by_category"]["parameters"]["required"] == ["category"]
    assert tools["extended_data_list_connectors_by_capability"]["parameters"]["required"] == ["capability"]


def test_catalog_tool_handlers_return_tier2_catalog_payloads() -> None:
    """Catalog MCP handlers should reuse the registry's Tier 2 payload surface."""
    tools = _catalog_tool_definitions()

    names = tools["extended_data_list_connectors"]["handler"]()
    available_names = tools["extended_data_list_available_connectors"]["handler"]()
    github = tools["extended_data_get_connector_info"]["handler"](name="github")
    categories = tools["extended_data_list_connector_categories"]["handler"]()
    repositories = tools["extended_data_list_connectors_by_capability"]["handler"](capability="repositories")

    assert isinstance(names, ExtendedList)
    assert "github" in names
    assert isinstance(available_names, ExtendedList)
    assert "cursor" in available_names
    assert set(available_names) <= set(names)
    assert isinstance(github, ExtendedDict)
    assert github["category"] == "development"
    assert "repositories" in github["capabilities"]
    assert isinstance(categories, ExtendedList)
    assert "cloud" in categories
    assert isinstance(repositories, ExtendedList)
    assert "github" in {connector["name"] for connector in repositories}


def test_catalog_tool_result_text_uses_shared_export_boundary() -> None:
    """Catalog MCP tool output should serialize like connector method output."""
    tools = _catalog_tool_definitions()
    payload = tools["extended_data_get_connector_info"]["handler"](name="github")

    text = _tool_result_text(payload)

    assert '"name": "github"' in text
    assert '"category": "development"' in text
    assert '"capabilities": [' in text


def test_jsonable_tool_result_lowers_extended_mapping_payloads() -> None:
    """MCP result serialization keeps Tier 2 mapping payloads as JSON objects."""
    payload = ExtendedDict({"service": {"name": "api"}})

    assert _jsonable_tool_result(payload) == {"service": {"name": "api"}}


def test_tool_result_text_uses_shared_export_boundary() -> None:
    """MCP text payloads should serialize through the Tier 3 export boundary."""
    payload = ExtendedDict({"service": {"name": "api"}})

    with patch(
        "extended_data.connectors.mcp.wrap_raw_data_for_export",
        wraps=mcp_module.wrap_raw_data_for_export,
    ) as mock_wrap_for_export:
        text = _tool_result_text(payload)

    assert '"service": {' in text
    mock_wrap_for_export.assert_called_once_with(
        {"service": {"name": "api"}},
        allow_encoding="json",
        indent_2=True,
        default=str,
    )


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


def test_tool_error_text_redacts_explicit_argument_values() -> None:
    """Generic MCP errors should redact caller-provided resource context."""
    error = RuntimeError("failed for private-user@example.com at /tmp/private%2Fpath while handling Fix login")

    text = _tool_error_text(
        error,
        values=[
            {
                "email": "private-user@example.com",
                "metadata": {"path": "/tmp/private/path", "prompt": "Fix login"},
            }
        ],
    )

    assert "private-user@example.com" not in text
    assert "/tmp/private%2Fpath" not in text
    assert "Fix login" not in text
    assert text.count("[REDACTED]") >= 3


def test_unknown_tool_text_redacts_sensitive_tool_names() -> None:
    """Generic MCP unknown-tool diagnostics should redact user-controlled names."""
    text = _unknown_tool_text("password=hunter2 Authorization: Bearer raw_token")

    assert "hunter2" not in text
    assert "raw_token" not in text
    assert "[REDACTED]" in text
