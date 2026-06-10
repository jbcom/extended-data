#!/usr/bin/env python3
"""File operation examples for Extended Data core library.

This module demonstrates file path utilities, encoding detection,
and file read/write operations provided by the library.
"""

from __future__ import annotations

import tempfile

from pathlib import Path

from extended_data import (
    FilePath,
    decode_file,
    file_path_depth,
    is_url,
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

        yaml_text = read_file(yaml_file)
        data = decode_file(yaml_text, file_path=yaml_file, as_extended=True)
        print(f"\nDecoded YAML file: {data}")
        print(f"YAML service keys: {data.flatten().keys()}")

        # Write and read JSON
        json_file = Path(tmpdir) / "data.json"
        json_content = '{"users": [{"id": 1, "name": "Alice"}]}'
        write_file(json_file, json_content)

        json_text = read_file(json_file)
        data = decode_file(json_text, file_path=json_file, as_extended=True)
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
