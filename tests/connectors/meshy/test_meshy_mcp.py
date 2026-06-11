"""Tests for Meshy MCP serialization helpers."""

from __future__ import annotations

from unittest.mock import patch

from extended_data.connectors.meshy import mcp as meshy_mcp_module
from extended_data.connectors.meshy.mcp import _jsonable_tool_result, _tool_error_payload, _tool_result_text
from extended_data.containers import ExtendedDict, ExtendedSet


def test_meshy_mcp_result_lowers_and_redacts_extended_payloads() -> None:
    """Meshy MCP result serialization should handle Tier 2 payloads directly."""
    payload = ExtendedDict(
        {
            "service": {"name": "meshy"},
            "password": "hunter2",
            "tags": ExtendedSet({"asset", "model"}),
        }
    )

    result = _jsonable_tool_result(payload)

    assert result["service"] == {"name": "meshy"}
    assert result["password"] == "[REDACTED]"
    assert sorted(result["tags"]) == ["asset", "model"]


def test_meshy_mcp_result_text_uses_shared_export_boundary() -> None:
    """Meshy MCP text payloads should serialize through the Tier 3 export boundary."""
    payload = ExtendedDict({"service": {"name": "meshy"}})

    with patch(
        "extended_data.connectors.meshy.mcp.wrap_raw_data_for_export",
        wraps=meshy_mcp_module.wrap_raw_data_for_export,
    ) as mock_wrap_for_export:
        text = _tool_result_text(payload)

    assert '"service": {' in text
    mock_wrap_for_export.assert_called_once_with(
        {"service": {"name": "meshy"}},
        allow_encoding="json",
        indent_2=True,
    )


def test_meshy_mcp_error_payload_redacts_sensitive_values() -> None:
    """Meshy MCP errors should not return raw secret-bearing exception text."""
    payload = _tool_error_payload(RuntimeError("failed api_key=key_123 Bearer raw_token"))

    assert "key_123" not in payload["error"]
    assert "raw_token" not in payload["error"]
    assert "[REDACTED]" in payload["error"]


def test_meshy_mcp_error_payload_redacts_unknown_tool_names() -> None:
    """Meshy MCP unknown-tool diagnostics should redact user-controlled names."""
    payload = _tool_error_payload("Unknown tool: password=hunter2 Authorization: Bearer raw_token")

    assert "hunter2" not in payload["error"]
    assert "raw_token" not in payload["error"]
    assert "[REDACTED]" in payload["error"]
