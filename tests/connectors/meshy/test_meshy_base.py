"""Tests for Meshy connector HTTP base helpers."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

from extended_data.connectors.meshy import base


def test_meshy_request_redacts_sensitive_error_body(monkeypatch: pytest.MonkeyPatch) -> None:
    """Meshy API errors should not expose raw response secrets."""
    mock_client = MagicMock()
    mock_client.request.return_value = httpx.Response(
        400,
        content=b'{"api_key":"key_123","message":"Authorization: Bearer raw_token"}',
    )

    monkeypatch.setattr(base, "_rate_limit", lambda: None)
    monkeypatch.setattr(base, "_headers", lambda: {"Authorization": "Bearer test"})
    monkeypatch.setattr(base, "get_client", lambda: mock_client)

    with pytest.raises(base.MeshyAPIError) as exc_info:
        base.request("GET", "text-to-3d")

    message = str(exc_info.value)
    assert exc_info.value.status_code == 400
    assert "key_123" not in message
    assert "raw_token" not in message
    assert "[REDACTED]" in message
