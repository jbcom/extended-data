#!/usr/bin/env python3
"""Serialization examples for the Extended Data core package.

This module demonstrates YAML, JSON, TOML, HCL, and Base64 encoding/decoding
utilities provided by the package.
"""

from __future__ import annotations

from extended_data import (
    base64_decode,
    base64_encode,
    decode_hcl2,
    decode_json,
    decode_toml,
    decode_yaml,
    encode_hcl2,
    encode_json,
    encode_toml,
    encode_yaml,
)


def demonstrate_yaml() -> None:
    """Demonstrate YAML encoding and decoding."""
    print("=== YAML Utilities ===\n")

    data = {
        "name": "example",
        "version": "1.0.0",
        "features": ["yaml", "json", "toml"],
        "config": {"debug": True, "port": 8080},
    }

    # Encode to YAML
    yaml_str = encode_yaml(data)
    print("Encoded YAML:")
    print(yaml_str)

    # Decode from YAML
    decoded = decode_yaml(yaml_str)
    print(f"Decoded data: {decoded}")


def demonstrate_json() -> None:
    """Demonstrate JSON encoding and decoding."""
    print("\n=== JSON Utilities ===\n")

    data = {
        "users": [
            {"id": 1, "name": "Alice", "active": True},
            {"id": 2, "name": "Bob", "active": False},
        ],
        "metadata": {"total": 2, "page": 1},
    }

    # Encode to JSON (uses orjson for speed)
    json_str = encode_json(data)
    print(f"Encoded JSON: {json_str}")

    # Decode from JSON
    decoded = decode_json(json_str)
    print(f"Decoded data: {decoded}")


def demonstrate_toml() -> None:
    """Demonstrate TOML encoding and decoding."""
    print("\n=== TOML Utilities ===\n")

    data = {
        "package": {"name": "my-app", "version": "0.1.0"},
        "dependencies": {"requests": ">=2.28.0", "pyyaml": ">=6.0"},
    }

    # Encode to TOML
    toml_str = encode_toml(data)
    print("Encoded TOML:")
    print(toml_str)

    # Decode from TOML
    decoded = decode_toml(toml_str)
    print(f"Decoded data: {decoded}")


def demonstrate_hcl() -> None:
    """Demonstrate HCL encoding and decoding."""
    print("\n=== HCL Utilities ===\n")

    data = {
        "locals": [{"region": "us-east-1"}],
        "resource": [
            {
                "aws_s3_bucket": {
                    "logs": {
                        "bucket": "my-log-bucket",
                        "acl": "private",
                    },
                },
            },
        ],
    }

    hcl_str = encode_hcl2(data)
    print("Encoded HCL:")
    print(hcl_str)

    decoded = decode_hcl2(hcl_str)
    print(f"Decoded data: {decoded}")


def demonstrate_base64() -> None:
    """Demonstrate Base64 encoding and decoding."""
    print("\n=== Base64 Utilities ===\n")

    # Simple string encoding
    text = "Hello, World!"
    encoded = base64_encode(text, wrap_raw_data=False)
    print(f"Original: {text}")
    print(f"Base64 encoded: {encoded}")

    # Decoding
    decoded = base64_decode(encoded, unwrap_raw_data=False)
    print(f"Raw decoded bytes: {decoded!r}")
    print(f"Decoded text: {decoded.decode('utf-8')}")

    # With data wrapping (useful for structured data)
    wrapped_encoded = base64_encode(text, wrap_raw_data=True)
    wrapped_decoded = base64_decode(wrapped_encoded, unwrap_raw_data=True)
    print(f"Wrapped decoded data: {wrapped_decoded}")


if __name__ == "__main__":
    demonstrate_yaml()
    demonstrate_json()
    demonstrate_toml()
    demonstrate_hcl()
    demonstrate_base64()
