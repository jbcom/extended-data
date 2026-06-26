#!/usr/bin/env python3
"""Basic usage example for InputProvider.

This example demonstrates the fundamental features of the InputProvider API:
- Loading inputs from environment variables
- Providing default values
- Type conversion (boolean, integer, float)
- Detached Tier 2 input snapshots
- Explicit input replacement
- Input freezing and thawing

Run with:
    python examples/inputs/basic_usage.py
"""

from __future__ import annotations

import os

from extended_data.inputs import InputProvider


def main() -> None:
    """Demonstrate basic InputProvider usage."""
    # Set up some environment variables for demonstration
    os.environ["APP_DEBUG"] = "true"
    os.environ["APP_PORT"] = "8080"
    os.environ["APP_TIMEOUT"] = "30.5"
    os.environ["APP_NAME"] = "MyApplication"

    # Initialize with environment variables filtered by prefix
    inputs = InputProvider(
        from_environment=True,
        env_prefix="APP_",
        strip_env_prefix=True,
    )

    # Retrieve inputs with type conversion
    inputs.get_input("DEBUG", is_bool=True)
    inputs.get_input("PORT", is_integer=True)
    inputs.get_input("TIMEOUT", is_float=True)
    inputs.get_input("NAME")
    inputs.inputs["NAME"].to_snake_case()
    inputs.snapshot_inputs()["NAME"].to_snake_case()

    # Demonstrate default values
    inputs.get_input("LOG_LEVEL", default="INFO")

    # Replace active inputs with a new promoted snapshot
    inputs.replace_inputs({"SERVICE": {"name": "api"}}, clear_frozen=True)
    inputs.snapshot_inputs()["SERVICE"]["name"].upper_first()

    # Demonstrate freeze/thaw functionality
    inputs.freeze_inputs()
    inputs.snapshot_inputs(frozen=True)["SERVICE"]["name"].upper_first()
    inputs.thaw_inputs()


if __name__ == "__main__":
    main()
