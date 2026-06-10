"""Common test fixtures for extended_data.logging tests.

This module provides shared fixtures for use across multiple test modules.
"""

from __future__ import annotations

import pytest

from extended_data.logging import Logging


@pytest.fixture
def logger() -> Logging:
    """Create a logger instance for testing with outputs disabled.

    Returns:
        Logging: A logger instance with console and file outputs disabled.
    """
    return Logging(enable_console=False, enable_file=False)
