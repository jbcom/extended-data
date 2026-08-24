---
title: Inputs Examples
description: Runnable examples rendered from their tested Python sources.
---

# Inputs Examples

## Basic Usage

[View source](https://github.com/jbcom/extended-data/blob/main/packages/extended-data/examples/inputs/basic_usage.py)

```python
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
```

## Decorator Api

[View source](https://github.com/jbcom/extended-data/blob/main/packages/extended-data/examples/inputs/decorator_api.py)

```python
#!/usr/bin/env python3
"""Decorator API example for Extended Data inputs.

This example demonstrates the modern decorator-based API:
- @directed_inputs class decorator
- @input_config method decorator for fine-grained control
- Automatic parameter injection from inputs
- JSON decoding from inputs

Run with:
    python examples/inputs/decorator_api.py
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

    @input_config("user_id", source_name="USER_ID", required=True)
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
        return f"Calling {endpoint} with configured API key"

    @input_config("config", source_name="CONFIG", decode_from_json=True)
    def parse_config(self, config: dict[str, str] | None = None) -> dict[str, str]:
        """Parse configuration from JSON input.

        The config parameter is automatically decoded from JSON.
        """
        return config or {}

    @input_config("port", source_name="PORT", is_integer=True, default=8080)
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
```

## Encoding Decoding

[View source](https://github.com/jbcom/extended-data/blob/main/packages/extended-data/examples/inputs/encoding_decoding.py)

```python
#!/usr/bin/env python3
"""Encoding and decoding example for Extended Data inputs.

This example demonstrates input decoding capabilities:
- JSON decoding
- YAML decoding
- Base64 decoding
- Combined Base64 + JSON/YAML decoding

Run with:
    python examples/inputs/encoding_decoding.py
"""

from __future__ import annotations

import base64

from extended_data.inputs import InputProvider


def main() -> None:
    """Demonstrate encoding/decoding features."""
    # Prepare encoded test data
    json_data = '{"database": "postgres", "port": "5432", "enabled": "true"}'
    yaml_data = "server:\n  host: localhost\n  port: 8080"
    base64_json = base64.b64encode(json_data.encode()).decode()
    base64_yaml = base64.b64encode(yaml_data.encode()).decode()

    inputs = InputProvider(
        inputs={
            "json_config": json_data,
            "yaml_config": yaml_data,
            "base64_json_config": base64_json,
            "base64_yaml_config": base64_yaml,
            "plain_text": "Hello, World!",
        },
        from_environment=False,
    )

    # JSON decoding
    json_config = inputs.decode_input("json_config", decode_from_json=True, as_extended=True)
    json_config.reconstruct_special_types().to_export_safe()

    # YAML decoding
    yaml_config = inputs.decode_input("yaml_config", decode_from_yaml=True, as_extended=True)
    yaml_config["server"]["host"].upper_first()

    # Base64 + JSON decoding
    base64_decoded_json = inputs.decode_input(
        "base64_json_config",
        decode_from_base64=True,
        decode_from_json=True,
        as_extended=True,
    )
    base64_decoded_json.wrap_for_export(allow_encoding="json")

    # Base64 + YAML decoding
    base64_decoded_yaml = inputs.decode_input(
        "base64_yaml_config",
        decode_from_base64=True,
        decode_from_yaml=True,
        as_extended=True,
    )
    base64_decoded_yaml.to_export_safe()

    # Plain text (no decoding)
    inputs.get_input("plain_text", as_extended=True).upper_first()

    # Missing input with default
    fallback = inputs.decode_input(
        "nonexistent",
        default={"fallback": "true"},
        decode_from_json=True,
        as_extended=True,
    )
    fallback.reconstruct_special_types()


if __name__ == "__main__":
    main()
```
