#!/usr/bin/env python3
"""Basic logging example for extended_data.logging.

This example demonstrates the fundamental logging capabilities of the
extended_data.logging package.
"""

from __future__ import annotations

from extended_data.logging import Logging


def main() -> None:
    """Run basic logging examples."""
    # Create a logger with console output enabled
    logger = Logging(enable_console=True, enable_file=False)

    # Basic message logging at different levels
    logger.logged_statement("Debug message", log_level="debug")
    logger.logged_statement("Info message", log_level="info")
    logger.logged_statement("Warning message", log_level="warning")
    logger.logged_statement("Error message", log_level="error")

    # Logging with JSON data attached
    user_data = {"username": "john_doe", "email": "john@example.com"}
    logger.logged_statement(
        "User logged in",
        json_data=user_data,
        log_level="info",
    )

    # Logging with labeled JSON data
    labeled_data = {
        "Request": {"method": "POST", "path": "/api/users"},
        "Response": {"status": 201, "body": {"id": 123}},
    }
    logger.logged_statement(
        "API request completed",
        labeled_json_data=labeled_data,
        log_level="info",
    )

    # Logging with identifiers
    logger.logged_statement(
        "Processing order",
        identifiers=["order_123", "customer_456"],
        log_level="info",
    )


if __name__ == "__main__":
    main()
