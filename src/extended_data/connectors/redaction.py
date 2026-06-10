"""Redaction helpers for connector output boundaries."""

from __future__ import annotations

import re

from collections.abc import Mapping
from typing import Any


SENSITIVE_KEY_PATTERN = (
    r"api[_-]?key|access[_-]?token|refresh[_-]?token|id[_-]?token|token|secret|password|passwd|pwd|"
    r"authorization|client[_-]?secret|private[_-]?key"
)
SENSITIVE_KEY_RE = re.compile(rf"(?i)^(?:{SENSITIVE_KEY_PATTERN})$")
JSON_SECRET_RE = re.compile(
    rf"(?i)([\"']?(?:{SENSITIVE_KEY_PATTERN})[\"']?\s*:\s*)"
    rf"([\"'][^\"']*[\"']|Bearer\s+[^\s,;}}\]]+|[^,\s}}\]]+)"
)
KEY_VALUE_SECRET_RE = re.compile(rf"(?i)(\b(?:{SENSITIVE_KEY_PATTERN})\b\s*=\s*)([^\s,;]+)")
CLI_SECRET_RE = re.compile(rf"(?i)(--(?:{SENSITIVE_KEY_PATTERN})(?:=|\s+))(\S+)")
BEARER_SECRET_RE = re.compile(r"(?i)(\bBearer\s+)[A-Za-z0-9._~+/=-]+")
REDACTED = "[REDACTED]"


def _redacted_value(value: str) -> str:
    """Return a redacted placeholder while preserving matching quotes."""
    quote = value[:1] if value[:1] in {"'", '"'} else ""
    return f"{quote}{REDACTED}{quote}"


def _redacted_field(match: re.Match[str]) -> str:
    """Return a redacted key/value field while preserving JSON shape."""
    prefix = match.group(1)
    value = match.group(2)
    if prefix.lstrip().startswith(('"', "'")) and value[:1] not in {"'", '"'}:
        return f'{prefix}"{REDACTED}"'
    return f"{prefix}{_redacted_value(value)}"


def redact_sensitive_text(message: Any) -> str:
    """Redact common secret fields in terminal-oriented text."""
    text = str(message)
    text = JSON_SECRET_RE.sub(_redacted_field, text)
    text = KEY_VALUE_SECRET_RE.sub(lambda match: f"{match.group(1)}{REDACTED}", text)
    text = CLI_SECRET_RE.sub(lambda match: f"{match.group(1)}{REDACTED}", text)
    return BEARER_SECRET_RE.sub(rf"\1{REDACTED}", text)


def redact_sensitive_data(value: Any) -> Any:
    """Recursively redact common secret fields in JSON-like connector data."""
    if isinstance(value, Mapping):
        redacted: dict[Any, Any] = {}
        for key, item in value.items():
            if isinstance(key, str) and SENSITIVE_KEY_RE.fullmatch(key):
                redacted[key] = REDACTED
            else:
                redacted[key] = redact_sensitive_data(item)
        return redacted
    if isinstance(value, list):
        return [redact_sensitive_data(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_sensitive_data(item) for item in value)
    if isinstance(value, set):
        return {redact_sensitive_data(item) for item in value}
    if isinstance(value, str):
        return redact_sensitive_text(value)
    return value
