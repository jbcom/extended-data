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

    # Example 2: Using unhump_results (shorthand for snake_case)
    logger.exit_run(results, unhump_results=True, exit_on_completion=False)

    # Example 3: Transform to camelCase
    snake_results = {"user_name": "john_doe", "email_address": "john@example.com"}
    logger.exit_run(snake_results, key_transform="camel_case", exit_on_completion=False)

    # Example 4: Nested key transformation
    nested_results = {
        "userData": {
            "firstName": "John",
            "lastName": "Doe",
            "contactInfo": {"phoneNumber": "555-1234"},
        }
    }
    logger.exit_run(nested_results, key_transform="snake_case", exit_on_completion=False)

    # Example 5: Adding prefix to keys
    field_results = {"item1": {"fieldName": "value1", "otherField": "value2"}}
    logger.exit_run(
        field_results,
        prefix="custom",
        exit_on_completion=False,
    )

    # Example 6: Custom transform function
    logger.exit_run(
        {"myKey": "value", "anotherKey": "data"},
        key_transform=lambda k: k.upper(),
        exit_on_completion=False,
    )


if __name__ == "__main__":
    main()
