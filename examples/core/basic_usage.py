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
