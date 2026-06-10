"""Tests for Meshy MCP serialization helpers."""

from __future__ import annotations

from extended_data.connectors.meshy.mcp import _jsonable_tool_result, _tool_error_payload
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


def test_meshy_mcp_error_payload_redacts_sensitive_values() -> None:
    """Meshy MCP errors should not return raw secret-bearing exception text."""
    payload = _tool_error_payload(RuntimeError("failed api_key=key_123 Bearer raw_token"))

    assert "key_123" not in payload["error"]
    assert "raw_token" not in payload["error"]
    assert "[REDACTED]" in payload["error"]
