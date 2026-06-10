#!/usr/bin/env python3
"""Example demonstrating verbosity control in extended_data.logging.

This example shows how to control which messages are logged based on
verbosity settings and bypass markers.
"""

from __future__ import annotations

from extended_data.logging import Logging


def main() -> None:
    """Run verbosity control examples."""
    # Create a logger with verbosity settings
    logger = Logging(
        enable_console=True,
        enable_file=False,
        enable_verbose_output=True,
        verbosity_threshold=2,  # Only show messages with verbosity <= 2
    )

    # This will be shown (verbosity 1 <= threshold 2)
    logger.logged_statement(
        "Important debug info",
        verbose=True,
        verbosity=1,
        log_level="debug",
    )

    # This will be shown (verbosity 2 <= threshold 2)
    logger.logged_statement(
        "Less important debug info",
        verbose=True,
        verbosity=2,
        log_level="debug",
    )

    # This will be suppressed (verbosity 3 > threshold 2)
    result = logger.logged_statement(
        "Very detailed debug info - this should NOT appear",
        verbose=True,
        verbosity=3,
        log_level="debug",
    )
    if result is None:
        pass

    # Register a bypass marker - messages with this marker ignore verbosity
    logger.register_verbosity_bypass_marker("CRITICAL_PATH")

    # This will be shown despite high verbosity because of bypass marker
    logger.logged_statement(
        "Critical path message - shown despite high verbosity",
        context_marker="CRITICAL_PATH",
        verbose=True,
        verbosity=5,
        log_level="debug",
    )


if __name__ == "__main__":
    main()
