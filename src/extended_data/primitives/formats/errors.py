"""Shared exceptions for Tier 1 format decoders."""

from __future__ import annotations

from typing import Any


class DataDecodeError(ValueError):
    """Raised when a supported data format cannot be decoded safely."""

    def __init__(
        self,
        format_name: str,
        *,
        reason: str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        """Initialize a sanitized decode error."""
        self.format_name = format_name
        self.reason = reason
        self.line = line
        self.column = column

        message = f"Failed to decode {format_name} data"
        if reason:
            message = f"{message}: {reason}"
        if line is not None:
            message = f"{message} at line {line}"
            if column is not None:
                message = f"{message}, column {column}"
        super().__init__(f"{message}.")

    @classmethod
    def from_exception(cls, format_name: str, exc: BaseException) -> DataDecodeError:
        """Build a sanitized decode error from a parser exception."""
        line, column = _get_error_position(exc)
        return cls(format_name, reason=_get_error_reason(exc), line=line, column=column)


def invalid_utf8_error(format_name: str) -> DataDecodeError:
    """Return a decode error for invalid UTF-8 input bytes."""
    return DataDecodeError(format_name, reason="input bytes are not valid UTF-8")


def _get_error_reason(exc: BaseException) -> str:
    """Extract a parser reason without including source snippets."""
    for attr in ("msg", "problem"):
        value = getattr(exc, attr, None)
        if isinstance(value, str) and value:
            return value.strip().replace("\n", " ")
    return type(exc).__name__


def _get_error_position(exc: BaseException) -> tuple[int | None, int | None]:
    """Extract one-based line and column data when the parser exposes it."""
    line = _as_int(getattr(exc, "lineno", None) or getattr(exc, "line", None))
    column = _as_int(getattr(exc, "colno", None) or getattr(exc, "col", None) or getattr(exc, "column", None))

    mark = getattr(exc, "problem_mark", None)
    if mark is not None:
        line = _as_int(getattr(mark, "line", None), offset=1)
        column = _as_int(getattr(mark, "column", None), offset=1)

    return line, column


def _as_int(value: Any, *, offset: int = 0) -> int | None:
    """Return an integer value plus offset, or None when unavailable."""
    if isinstance(value, int):
        return value + offset
    return None
