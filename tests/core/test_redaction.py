"""Tests for Tier 1 redaction helpers."""

from __future__ import annotations

from extended_data.primitives.redaction import redact_sensitive_data, redact_sensitive_text


def test_redact_sensitive_text_preserves_json_shape() -> None:
    """Terminal text redaction should keep JSON-ish values parseable."""
    message = '{"password": "hunter2", "id_token": 12345, "Authorization": Bearer raw_token}'

    redacted = redact_sensitive_text(message)

    assert "hunter2" not in redacted
    assert "12345" not in redacted
    assert "raw_token" not in redacted
    assert '"password": "[REDACTED]"' in redacted
    assert '"id_token": "[REDACTED]"' in redacted
    assert '"Authorization": "[REDACTED]"' in redacted


def test_redact_sensitive_data_recurses_through_json_like_payloads() -> None:
    """Structured redaction should handle nested JSON-like data."""
    payload = {
        "password": "hunter2",
        "nested": [{"api_key": "key_123", "value": "ok"}],
        "headers": {"authorization": "Bearer raw_token"},
        "message": "client_secret=secret_123",
    }

    redacted = redact_sensitive_data(payload)

    assert redacted == {
        "password": "[REDACTED]",
        "nested": [{"api_key": "[REDACTED]", "value": "ok"}],
        "headers": {"authorization": "[REDACTED]"},
        "message": "client_secret=[REDACTED]",
    }
