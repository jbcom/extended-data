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


def test_redact_sensitive_text_accepts_known_diagnostic_values() -> None:
    """Callers can redact known resource identifiers that are sensitive in context."""
    message = "failed for user@example.com and user%40example.com with token=raw_token"

    redacted = redact_sensitive_text(message, values=["user@example.com"])

    assert "user@example.com" not in redacted
    assert "user%40example.com" not in redacted
    assert "raw_token" not in redacted
    assert redacted.count("[REDACTED]") == 3


def test_redact_sensitive_text_preserves_non_secret_url_query_values() -> None:
    """Key/value redaction should not consume unrelated URL query parameters."""
    message = "https://example.com/config.json?api_key=key_123&region=us-east-1"

    redacted = redact_sensitive_text(message)

    assert "key_123" not in redacted
    assert "api_key=[REDACTED]" in redacted
    assert "region=us-east-1" in redacted


def test_redact_sensitive_text_flattens_nested_known_values() -> None:
    """Caller-provided diagnostic context can be nested like CLI or MCP arguments."""
    message = "failed for user@example.com at /tmp/private%2Fpath using prompt Fix login"

    redacted = redact_sensitive_text(
        message,
        values=[{"email": "user@example.com", "paths": ["/tmp/private/path"], "prompt": "Fix login"}],
    )

    assert "user@example.com" not in redacted
    assert "/tmp/private%2Fpath" not in redacted
    assert "Fix login" not in redacted
    assert redacted.count("[REDACTED]") == 3


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


def test_redact_sensitive_data_applies_known_values_recursively() -> None:
    """Structured redaction should carry caller-provided sensitive values through nested text."""
    payload = {"details": ["private/path", {"message": "see private%2Fpath"}]}

    redacted = redact_sensitive_data(payload, values=["private/path"])

    assert redacted == {"details": ["[REDACTED]", {"message": "see [REDACTED]"}]}
