---
title: Logging Examples
description: Runnable examples rendered from their tested Python sources.
---

# Logging Examples

## Basic Logging

[View source](https://github.com/jbcom/extended-data/blob/main/packages/extended-data/examples/logging/basic_logging.py)

```python
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
```

## Exit Run Formatting

[View source](https://github.com/jbcom/extended-data/blob/main/packages/extended-data/examples/logging/exit_run_formatting.py)

```python
#!/usr/bin/env python3
"""Example demonstrating exit_run result formatting.

This example shows how to use exit_run to format and transform results
for output, including key transformations and prefixing.
"""

from __future__ import annotations

from extended_data.logging import Logging


def main() -> None:
    """Run exit_run formatting examples."""
    logger = Logging(enable_console=False, enable_file=False)

    # Example 1: Basic key transformation (camelCase to snake_case)
    results = {
        "userName": "john_doe",
        "emailAddress": "john@example.com",
        "createdAt": "2025-01-01T00:00:00Z",
    }
    logger.exit_run(results, key_transform="snake_case", exit_on_completion=False)

    # Example 2: Transform to camelCase
    snake_results = {"user_name": "john_doe", "email_address": "john@example.com"}
    logger.exit_run(snake_results, key_transform="camel_case", exit_on_completion=False)

    # Example 3: Nested key transformation
    nested_results = {
        "userData": {
            "firstName": "John",
            "lastName": "Doe",
            "contactInfo": {"phoneNumber": "555-1234"},
        }
    }
    logger.exit_run(nested_results, key_transform="snake_case", exit_on_completion=False)

    # Example 4: Adding prefix to keys
    field_results = {"item1": {"fieldName": "value1", "otherField": "value2"}}
    logger.exit_run(
        field_results,
        prefix="custom",
        exit_on_completion=False,
    )

    # Example 5: Custom transform function
    logger.exit_run(
        {"myKey": "value", "anotherKey": "data"},
        key_transform=lambda k: k.upper(),
        exit_on_completion=False,
    )


if __name__ == "__main__":
    main()
```

## Markers And Storage

[View source](https://github.com/jbcom/extended-data/blob/main/packages/extended-data/examples/logging/markers_and_storage.py)

```python
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
```

## Verbosity Control

[View source](https://github.com/jbcom/extended-data/blob/main/packages/extended-data/examples/logging/verbosity_control.py)

```python
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
```
