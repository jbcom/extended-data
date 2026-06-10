#!/usr/bin/env python3
"""Example demonstrating context markers and message storage.

This example shows how to use context markers to prefix messages and
storage markers to collect messages for later retrieval.
"""

from __future__ import annotations

from extended_data.logging import Logging


def main() -> None:
    """Run marker and storage examples."""
    # Create a logger with a default storage marker
    logger = Logging(
        enable_console=True,
        enable_file=False,
        default_storage_marker="general",
    )

    # Messages with context markers get prefixed
    logger.logged_statement(
        "Starting database connection",
        context_marker="DATABASE",
        log_level="info",
    )

    logger.logged_statement(
        "Query executed successfully",
        context_marker="DATABASE",
        log_level="debug",
    )

    # Messages with storage markers are collected
    logger.logged_statement(
        "User registration started",
        storage_marker="user_events",
        log_level="info",
    )

    logger.logged_statement(
        "User registration completed",
        storage_marker="user_events",
        log_level="info",
    )

    # Using both context and storage markers together
    logger.logged_statement(
        "Payment processed",
        context_marker="PAYMENT",
        storage_marker="transactions",
        log_level="info",
    )

    # Access stored messages through a detached promoted snapshot
    for messages in logger.snapshot_stored_messages().values():
        for _msg in messages:
            print(_msg)


if __name__ == "__main__":
    main()
