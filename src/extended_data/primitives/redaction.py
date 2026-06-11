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


def _iter_known_values(values: Iterable[Any]) -> Iterable[Any]:
    """Yield scalar known-sensitive values from nested caller context."""
    for value in values:
        if value is None:
            continue
        if isinstance(value, Mapping):
            yield from _iter_known_values(value.values())
        elif isinstance(value, (str, bytes, bytearray)):
            yield value
        elif isinstance(value, Iterable):
            yield from _iter_known_values(value)
        else:
            yield value


def _slash_encoding_variants(value: str) -> set[str]:
    """Return common variants where any slash positions are URL encoded."""
    slash_count = value.count("/")
    if slash_count == 0 or slash_count > 8:
        return set()

    variants: set[str] = set()
    for mask in range(1, 1 << slash_count):
        slash_index = 0
        parts: list[str] = []
        for char in value:
            if char == "/":
                parts.append("%2F" if mask & (1 << slash_index) else "/")
                slash_index += 1
            else:
                parts.append(char)
        variants.add("".join(parts))
    return variants


def _redact_known_values(text: str, values: Iterable[Any] | None) -> str:
    """Redact explicitly provided values and URL-encoded variants."""
    if values is None:
        return text
    for value in _iter_known_values(values):
        raw_value = str(value)
        if not raw_value:
            continue
        slash_encoded = raw_value.replace("/", "%2F")
        candidates = {
            raw_value,
            quote(raw_value, safe=""),
            quote(raw_value, safe="/"),
            slash_encoded,
        }
        candidates.update(_slash_encoding_variants(raw_value))
        for candidate in set(candidates) | {candidate.replace("%2F", "%2f") for candidate in candidates}:
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
