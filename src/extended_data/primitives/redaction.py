"""Tier 1 redaction helpers for diagnostics and JSON-like data."""

from __future__ import annotations

import re

from collections.abc import Iterable, Mapping
from typing import Any
from urllib.parse import quote


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


def _redact_known_values(text: str, values: Iterable[Any] | None) -> str:
    """Redact explicitly provided values and URL-encoded variants."""
    if values is None:
        return text
    for value in values:
        if value is None:
            continue
        raw_value = str(value)
        if not raw_value:
            continue
        for candidate in {raw_value, quote(raw_value, safe="")}:
            text = text.replace(candidate, REDACTED)
    return text


def redact_sensitive_text(message: Any, *, values: Iterable[Any] | None = None) -> str:
    """Redact common secret fields in terminal-oriented text."""
    text = str(message)
    text = JSON_SECRET_RE.sub(_redacted_field, text)
    text = KEY_VALUE_SECRET_RE.sub(lambda match: f"{match.group(1)}{REDACTED}", text)
    text = CLI_SECRET_RE.sub(lambda match: f"{match.group(1)}{REDACTED}", text)
    text = BEARER_SECRET_RE.sub(rf"\1{REDACTED}", text)
    return _redact_known_values(text, values)


def redact_sensitive_data(value: Any, *, values: Iterable[Any] | None = None) -> Any:
    """Recursively redact common secret fields in JSON-like data."""
    if isinstance(value, Mapping):
        redacted: dict[Any, Any] = {}
        for key, item in value.items():
            if isinstance(key, str) and SENSITIVE_KEY_RE.fullmatch(key):
                redacted[key] = REDACTED
            else:
                redacted[key] = redact_sensitive_data(item, values=values)
        return redacted
    if isinstance(value, list):
        return [redact_sensitive_data(item, values=values) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_sensitive_data(item, values=values) for item in value)
    if isinstance(value, set):
        return {redact_sensitive_data(item, values=values) for item in value}
    if isinstance(value, str):
        return redact_sensitive_text(value, values=values)
    return value
