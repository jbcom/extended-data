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
