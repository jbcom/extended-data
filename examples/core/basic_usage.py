#!/usr/bin/env python3
"""Basic usage examples for Extended Data core."""

from __future__ import annotations

from extended_data import (
    all_non_empty,
    any_non_empty,
    deep_merge,
    filter_list,
    filter_map,
    first_non_empty,
    flatten_list,
    flatten_map,
    is_nothing,
    removeprefix,
    removesuffix,
    sanitize_key,
    truncate,
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
    nested = ["api", ["worker", ["scheduler"]], "docs"]
    print("Flattened:", flatten_list(nested))

    items = ["apple", "banana", "apricot", "cherry"]
    print("Allowlist:", filter_list(items, allowlist=["apple", "apricot"]))
    print("Denylist:", filter_list(items, denylist=["banana"]))


def demonstrate_map_utilities() -> None:
    """Demonstrate map merge, flatten, and filtering helpers."""
    print("\n=== Map Utilities ===")
    base = {"service": {"debug": False, "host": "localhost"}}
    override = {"service": {"debug": True, "port": 8080}}
    print("Deep merge:", deep_merge(base, override))

    nested = {"service": {"http": {"port": 8080}}, "enabled": True}
    print("Flattened:", flatten_map(nested))

    payload = {"name": "api", "age": 30, "city": "Chicago", "active": True}
    kept, removed = filter_map(payload, allowlist=["name", "city"])
    print("Filtered map:", kept)
    print("Removed map:", removed)


def demonstrate_string_utilities() -> None:
    """Demonstrate basic string cleanup helpers."""
    print("\n=== String Utilities ===")
    text = "prefix_content_suffix"
    print("Remove prefix:", removeprefix(text, "prefix_"))
    print("Remove suffix:", removesuffix(text, "_suffix"))
    print("Truncate:", truncate("This value is intentionally too long", 20))
    print("Sanitize key:", sanitize_key("User Name (Primary)"))


if __name__ == "__main__":
    demonstrate_state_utilities()
    demonstrate_list_utilities()
    demonstrate_map_utilities()
    demonstrate_string_utilities()
