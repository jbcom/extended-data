"""This module provides utilities for string and value matching.

It includes functions to partially match strings and to compare non-empty values
for equality, handling different data types including strings, mappings, and lists.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from extended_data.primitives.state import is_nothing
from extended_data.primitives.types import make_hashable


def is_partial_match(
    a: str | None,
    b: str | None,
    check_prefix_only: bool = False,
) -> bool:
    """Checks if two strings partially match.

    Args:
        a (str | None): The first string.
        b (str | None): The second string.
        check_prefix_only (bool): Whether to check only the prefix.

    Returns:
        bool: True if there is a partial match, False otherwise.
    """
    if is_nothing(a) or is_nothing(b):
        return False

    # Convert strings to lowercase for case-insensitive comparison
    a = a.casefold() if a else ""
    b = b.casefold() if b else ""

    # Check if one string is a prefix of the other
    if check_prefix_only:
        return a.startswith(b) or b.startswith(a)

    # Check if one string is contained within the other
    return a in b or b in a


def is_non_empty_match(a: Any, b: Any) -> bool:
    """Checks if two non-empty values match.

    Args:
        a (Any): The first value.
        b (Any): The second value.

    Returns:
        bool: True if the values match, False otherwise.
    """
    if is_nothing(a) or is_nothing(b):
        return False

    # Ensure both values are of the same type
    if not isinstance(a, type(b)):
        return False

    # Handle string comparisons case-insensitively
    if isinstance(a, str):
        a = a.casefold()
        b = b.casefold()
    # Normalize composite structures without mutating caller-owned values.
    elif isinstance(a, Mapping):
        a = make_hashable(a)
        b = make_hashable(b)
    elif isinstance(a, list) and isinstance(b, list):
        a = tuple(sorted((make_hashable(item) for item in a), key=repr))
        b = tuple(sorted((make_hashable(item) for item in b), key=repr))
    elif isinstance(a, (set, frozenset)) and isinstance(b, (set, frozenset)):
        a = frozenset(make_hashable(item) for item in a)
        b = frozenset(make_hashable(item) for item in b)
    elif isinstance(a, tuple) and isinstance(b, tuple):
        a = tuple(make_hashable(item) for item in a)
        b = tuple(make_hashable(item) for item in b)

    # Return comparison result
    return a == b
