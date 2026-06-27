"""Type definitions for the logging module."""

from __future__ import annotations

from typing import Literal, TypeAlias


LogLevel: TypeAlias = Literal["debug", "info", "warning", "error", "fatal", "critical"]
"""A type alias representing the valid log levels used in the logging module.

Valid values are:
- "debug"
- "info"
- "warning"
- "error"
- "fatal"
- "critical"
"""
