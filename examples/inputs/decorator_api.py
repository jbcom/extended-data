#!/usr/bin/env python3
"""Decorator API example for Extended Data inputs.

This example demonstrates the modern decorator-based API:
- @directed_inputs class decorator
- @input_config method decorator for fine-grained control
- Automatic parameter injection from inputs
- JSON decoding from inputs

Run with:
    python -m examples.decorator_api
"""

from __future__ import annotations

import os

from extended_data.inputs import directed_inputs, input_config


@directed_inputs(
    from_environment=True,
    env_prefix="SERVICE_",
    strip_env_prefix=True,
)
class UserService:
    """Example service demonstrating decorator-based input handling."""

    def get_user(self, user_id: str) -> dict[str, str]:
        """Get a user by ID.

        The user_id parameter is automatically populated from inputs
        if not provided explicitly.
        """
        return {"id": user_id, "name": f"User {user_id}"}

    @input_config("api_key", source_name="API_KEY", required=True)
    def authenticated_call(self, api_key: str, endpoint: str = "/users") -> str:
        """Make an authenticated API call.

        The api_key is required and sourced from API_KEY input.
        The endpoint parameter uses its default if not in inputs.
        """
        return f"Calling {endpoint} with key {api_key[:4]}..."

    @input_config("config", decode_from_json=True)
    def parse_config(self, config: dict[str, str] | None = None) -> dict[str, str]:
        """Parse configuration from JSON input.

        The config parameter is automatically decoded from JSON.
        """
        return config or {}

    @input_config("port", is_integer=True, default=8080)
    def get_port(self, port: int) -> int:
        """Get the configured port.

        Demonstrates type coercion with defaults.
        """
        return port


def main() -> None:
    """Demonstrate decorator API usage."""
    # Set up environment variables (use your own values in production)
    os.environ["SERVICE_USER_ID"] = "12345"
    os.environ["SERVICE_API_KEY"] = "test-only-example-key"
    os.environ["SERVICE_CONFIG"] = '{"host": "localhost", "debug": "true"}'
    os.environ["SERVICE_PORT"] = "9000"

    # Create service instance - inputs are automatically loaded
    service = UserService()

    # Method parameters are auto-populated from inputs
    service.get_user()  # user_id comes from SERVICE_USER_ID

    # Required inputs with custom source names
    service.authenticated_call()  # api_key from SERVICE_API_KEY

    # JSON decoding
    service.parse_config()  # Decoded from SERVICE_CONFIG

    # Type coercion
    service.get_port()  # Converted to int from SERVICE_PORT

    # Override inputs at instantiation
    custom_service = UserService(_input_provider_config={"inputs": {"USER_ID": "custom-999"}})
    custom_service.get_user()

    # Explicit arguments always win
    service.get_user(user_id="explicit-user")


if __name__ == "__main__":
    main()
