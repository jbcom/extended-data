---
title: Core Examples
description: Runnable examples rendered from their tested Python sources.
---

# Core Examples

## Basic Usage

[View source](https://github.com/jbcom/extended-data/blob/main/packages/extended-data/examples/core/basic_usage.py)

```python
#!/usr/bin/env python3
"""Basic usage examples for Extended Data core."""

from __future__ import annotations

from extended_data import (
    ExtendedDict,
    ExtendedList,
    ExtendedString,
)
from extended_data.primitives import (
    all_non_empty,
    any_non_empty,
    first_non_empty,
    is_nothing,
)


def demonstrate_state_utilities() -> None:
    """Demonstrate state helper behavior."""
    print("=== State Utilities ===")
    state = {"name": "worker", "region": "", "enabled": True}
    print("Is empty string nothing:", is_nothing(""))
    print("Any non-empty:", any_non_empty(state, "region", "name"))
    print("All non-empty:", all_non_empty(state["name"], state["enabled"]))
    print("First non-empty:", first_non_empty(None, "", "fallback"))


def demonstrate_list_utilities() -> None:
    """Demonstrate list flattening and allowlist/denylist filtering."""
    print("\n=== List Utilities ===")
    nested = ExtendedList(["api", ["worker", ["scheduler"]], "docs"])
    print("Flattened:", nested.flatten())

    items = ExtendedList(["apple", "banana", "apricot", "cherry"])
    print("Allowlist:", items.filter_values(allowlist=["apple", "apricot"]))
    print("Denylist:", items.filter_values(denylist=["banana"]))


def demonstrate_map_utilities() -> None:
    """Demonstrate map merge, flatten, and filtering helpers."""
    print("\n=== Map Utilities ===")
    base = ExtendedDict({"service": {"debug": False, "host": "localhost"}})
    override = {"service": {"debug": True, "port": 8080}}
    print("Deep merge:", base.deep_merge(override))

    nested = ExtendedDict({"service": {"http": {"port": 8080}}, "enabled": True})
    print("Flattened:", nested.flatten())

    payload = ExtendedDict({"name": "api", "age": 30, "city": "Chicago", "active": True})
    kept, removed = payload.filter(allowlist=["name", "city"])
    print("Filtered map:", kept)
    print("Removed map:", removed)


def demonstrate_string_utilities() -> None:
    """Demonstrate basic string cleanup helpers."""
    print("\n=== String Utilities ===")
    text = ExtendedString("prefix_content_suffix")
    print("Remove prefix:", text.remove_prefix("prefix_"))
    print("Remove suffix:", text.remove_suffix("_suffix"))
    print("Truncate:", ExtendedString("This value is intentionally too long").truncate(20))
    print("Sanitize key:", ExtendedString("User Name (Primary)").sanitize())


if __name__ == "__main__":
    demonstrate_state_utilities()
    demonstrate_list_utilities()
    demonstrate_map_utilities()
    demonstrate_string_utilities()
```

## Composed Workflows

[View source](https://github.com/jbcom/extended-data/blob/main/packages/extended-data/examples/core/composed_workflows.py)

```python
#!/usr/bin/env python3
"""End-to-end workflow examples for Extended Data core.

This script demonstrates how package primitives, containers, and processors
compose into complete configuration and payload pipelines.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from extended_data import (
    DataWorkflow,
    ExtendedList,
    base64_decode,
    base64_encode,
    list_data_transform_steps,
    read_data_file,
    read_file,
    write_file,
)
from extended_data.primitives import decode_hcl2, encode_hcl2
from extended_data.primitives.formats.yaml import YamlTagged


def demonstrate_layered_config_workflow() -> None:
    """Read, decode, merge, and write structured configuration."""
    print("=== Layered Config Workflow ===\n")

    base_config = {
        "service": {"name": "api", "debug": False},
        "ports": [8080],
        "features": {"auth": True},
    }
    env_config = {
        "service": {"debug": True},
        "ports": [8081],
        "features": {"metrics": True},
    }

    with TemporaryDirectory() as tmpdir:
        tld = Path(tmpdir)
        write_file("config/base.yaml", base_config, tld=tld)
        write_file("config/dev.yaml", env_config, tld=tld)

        env_data = DataWorkflow.from_file("config/dev.yaml", tld=tld).value
        result = (
            DataWorkflow.from_file("config/base.yaml", tld=tld)
            .merge(env_data, name="merge-env")
            .write("build/config.yaml", tld=tld)
        )
        result.to_export_safe()
        merged_text = read_file("build/config.yaml", tld=tld)

    print(merged_text)
    print(f"Steps: {', '.join(result.steps)}")


def demonstrate_terraform_handoff_workflow() -> None:
    """Show HCL data moving through raw text and Base64 transport."""
    print("\n=== Terraform Handoff Workflow ===\n")

    terraform = {
        "locals": [{"region": "us-east-1"}],
        "resource": [
            {
                "aws_s3_bucket": {
                    "logs": {
                        "bucket": "my-logs-bucket",
                        "acl": "private",
                    }
                }
            }
        ],
    }

    hcl_text = encode_hcl2(terraform)
    wrapped = base64_encode(hcl_text, wrap_raw_data=False)
    decoded_bytes = base64_decode(wrapped, unwrap_raw_data=False)

    print(hcl_text)
    print(f"\nTransport characters: {len(wrapped)}")
    print(f"Raw decoded bytes: {len(decoded_bytes)}")
    print(f"\nRound-tripped: {decode_hcl2(decoded_bytes) == terraform}")


def demonstrate_api_payload_workflow() -> None:
    """Normalize and serialize an API-style payload."""
    print("\n=== API Payload Workflow ===\n")

    payload = {
        "HTTPResponseCode": "200",
        "SelectedServices": ["api", "worker", "db", "api"],
        "Tags": ["api", "api", "docs"],
        "EmptyValue": "",
    }

    def select_services(data):
        return data | {"SelectedServices": ExtendedList(data["SelectedServices"]).filter_values(denylist=["db"])}

    workflow = (
        DataWorkflow.from_value(payload)
        .then(("select-services", select_services))
        .transform("reconstruct", "deduplicate", "compact", "unhump")
    )
    normalized = workflow.result().value

    with TemporaryDirectory() as tmpdir:
        tld = Path(tmpdir)
        write_file("build/payload.json", normalized, tld=tld)
        payload_text = read_file("build/payload.json", tld=tld)

    print(payload_text)
    print(f"Steps: {', '.join(workflow.steps)}")
    print(f"Known transforms: {', '.join(list_data_transform_steps())}")


def demonstrate_yaml_native_workflow() -> None:
    """Preserve YAML-native wrappers through the root file helpers."""
    print("\n=== YAML-Native Workflow ===\n")

    template = {
        "bucket_name": YamlTagged("!Ref", "BucketName"),
        "script": "echo one\necho two",
    }

    with TemporaryDirectory() as tmpdir:
        tld = Path(tmpdir)
        write_file("template.yaml", template, tld=tld)
        rendered = read_file("template.yaml", tld=tld)
        decoded = read_data_file("template.yaml", tld=tld)

    print(rendered)
    print(f"\nDecoded tag: {decoded['bucket_name'].tag}")


if __name__ == "__main__":
    demonstrate_layered_config_workflow()
    demonstrate_terraform_handoff_workflow()
    demonstrate_api_payload_workflow()
    demonstrate_yaml_native_workflow()
```

## File Operations

[View source](https://github.com/jbcom/extended-data/blob/main/packages/extended-data/examples/core/file_operations.py)

```python
#!/usr/bin/env python3
"""File operation examples for the Extended Data core package.

This module demonstrates file path utilities, encoding detection,
and file read/write operations provided by the package.
"""

from __future__ import annotations

import tempfile

from pathlib import Path

from extended_data import (
    FilePath,
    file_path_depth,
    is_url,
    read_data_file,
    read_file,
    resolve_local_path,
    write_file,
)


def demonstrate_filepath_type() -> None:
    """Demonstrate the FilePath type and related utilities."""
    print("=== FilePath Utilities ===\n")

    # FilePath accepts both str and Path
    path1: FilePath = "/home/user/documents/file.txt"
    path2: FilePath = Path("/home/user/documents/file.txt")

    print(f"String path: {path1}")
    print(f"Path object: {path2}")

    # Calculate path depth
    paths = [
        "/home/user/file.txt",
        "/home/user/docs/project/readme.md",
        "relative/path/to/file.py",
    ]

    print("\nPath depths:")
    for p in paths:
        print(f"  '{p}': depth = {file_path_depth(p)}")


def demonstrate_url_detection() -> None:
    """Demonstrate URL detection."""
    print("\n=== URL Detection ===\n")

    test_strings = [
        "https://example.com/path/to/file",
        "http://localhost:8080",
        "/home/user/file.txt",
        "relative/path.txt",
        "ftp://files.example.com/data",
    ]

    for s in test_strings:
        print(f"is_url('{s}'): {is_url(s)}")


def demonstrate_file_operations() -> None:
    """Demonstrate file read/write operations."""
    print("\n=== File Operations ===\n")

    # Create a temporary directory for demo
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write a file
        test_file = Path(tmpdir) / "test.txt"
        content = "Hello, extended-data!\nThis is a test file."

        write_file(test_file, content)
        print(f"Wrote file: {test_file}")

        # Read the file back
        read_content = read_file(test_file)
        print(f"Read content:\n{read_content}")

        # Write and read YAML
        yaml_file = Path(tmpdir) / "config.yaml"
        yaml_content = """
name: example
version: 1.0.0
settings:
  debug: true
  port: 8080
"""
        write_file(yaml_file, yaml_content)

        data = read_data_file(yaml_file)
        print(f"\nDecoded YAML file: {data}")
        print(f"YAML service keys: {data.flatten().keys()}")

        # Write and read JSON
        json_file = Path(tmpdir) / "data.json"
        json_content = '{"users": [{"id": 1, "name": "Alice"}]}'
        write_file(json_file, json_content)

        data = read_data_file(json_file)
        print(f"Decoded JSON file: {data}")


def demonstrate_path_resolution() -> None:
    """Demonstrate path resolution utilities."""
    print("\n=== Path Resolution ===\n")

    # Resolve paths relative to a base
    base_path = Path.cwd()
    relative_paths = ["src/main.py", "../parent/file.txt", "./current/file.txt"]

    print(f"Base path: {base_path}")
    for rel in relative_paths:
        resolved = resolve_local_path(rel, tld=base_path)
        print(f"  '{rel}' -> {resolved}")


if __name__ == "__main__":
    demonstrate_filepath_type()
    demonstrate_url_detection()
    demonstrate_file_operations()
    demonstrate_path_resolution()
```

## Serialization

[View source](https://github.com/jbcom/extended-data/blob/main/packages/extended-data/examples/core/serialization.py)

```python
#!/usr/bin/env python3
"""Serialization examples for the Extended Data core package.

This module demonstrates YAML, JSON, TOML, HCL, and Base64 encoding/decoding
utilities provided by the package.
"""

from __future__ import annotations

from extended_data import (
    base64_decode,
    base64_encode,
)
from extended_data.primitives import (
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
```

## String Transformations

[View source](https://github.com/jbcom/extended-data/blob/main/packages/extended-data/examples/core/string_transformations.py)

```python
#!/usr/bin/env python3
"""String transformation examples for the Extended Data core package.

This module demonstrates case conversion, humanization, pluralization,
and other string manipulation utilities provided by the package.
"""

from __future__ import annotations

from extended_data.primitives import (
    humanize,
    ordinalize,
    pluralize,
    singularize,
    titleize,
    to_camel_case,
    to_kebab_case,
    to_pascal_case,
    to_snake_case,
)


def demonstrate_case_conversion() -> None:
    """Demonstrate case conversion utilities."""
    examples = [
        "hello_world",
        "my-variable-name",
        "SomeClassName",
        "user_account_settings",
    ]

    print("=== Case Conversion ===\n")

    print("-- to_camel_case --")
    for text in examples:
        print(f"  to_camel_case({text!r}) -> {to_camel_case(text)!r}")

    print("\n-- to_pascal_case --")
    for text in examples:
        print(f"  to_pascal_case({text!r}) -> {to_pascal_case(text)!r}")

    print("\n-- to_snake_case --")
    for text in examples:
        print(f"  to_snake_case({text!r}) -> {to_snake_case(text)!r}")

    print("\n-- to_kebab_case --")
    for text in examples:
        print(f"  to_kebab_case({text!r}) -> {to_kebab_case(text)!r}")

    print()


def demonstrate_humanization() -> None:
    """Demonstrate string humanization."""
    examples = [
        "user_id",
        "createdAt",
        "HTTPResponse",
        "employee_salary_amount",
    ]

    print("=== Humanization ===\n")

    print("-- humanize --")
    for example in examples:
        print(f"  humanize({example!r}) -> {humanize(example)!r}")

    print("\n-- titleize --")
    for example in examples:
        print(f"  titleize({example!r}) -> {titleize(example)!r}")

    print()


def demonstrate_pluralization() -> None:
    """Demonstrate pluralization and singularization."""
    words = ["cat", "child", "person", "mouse", "analysis", "octopus"]

    print("=== Pluralization ===\n")

    print("-- pluralize --")
    for word in words:
        print(f"  pluralize({word!r}) -> {pluralize(word)!r}")

    print("\n-- singularize --")
    plural_words = ["cats", "children", "people", "mice", "analyses", "octopi"]
    for word in plural_words:
        print(f"  singularize({word!r}) -> {singularize(word)!r}")

    print()


def demonstrate_ordinalization() -> None:
    """Demonstrate number ordinalization."""
    numbers = [1, 2, 3, 4, 11, 12, 13, 21, 22, 23, 100, 101, 102, 103]

    print("=== Ordinalization ===\n")

    for num in numbers:
        print(f"  ordinalize({num}) -> {ordinalize(num)!r}")

    print()


if __name__ == "__main__":
    demonstrate_case_conversion()
    demonstrate_humanization()
    demonstrate_pluralization()
    demonstrate_ordinalization()
```
