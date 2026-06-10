"""Lifecycle logging package for comprehensive application logging.

This package provides utilities for managing application lifecycle logs, including
configurable logging for console and file outputs, and clean exit functionality.
"""

from __future__ import annotations

from extended_data._version import __version__
from extended_data.logging.logging import ExitRunError, KeyTransform, Logging


__all__ = ["ExitRunError", "KeyTransform", "Logging", "__version__"]
