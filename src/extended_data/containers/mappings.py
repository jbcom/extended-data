"""Extended mapping container built on Tier 1 primitives."""

from __future__ import annotations

from collections import UserDict
from collections.abc import Mapping
from typing import Any

from extended_data.primitives.mappings import (
    all_values_from_map,
    deduplicate_map,
    deep_merge,
    filter_map,
    first_non_empty_value_from_map,
    flatten_map,
    unhump_map,
)
from extended_data.primitives.state import all_non_empty_in_dict


class ExtendedDict(UserDict[str, Any]):
    """Dictionary wrapper with chainable primitive operations."""

    def __init__(self, initialdata: Mapping[str, Any] | None = None, **kwargs: Any) -> None:
        """Initialize the extended dictionary."""
        super().__init__(dict(initialdata or {}, **kwargs))

    def deep_merge(self, *mappings: Mapping[str, Any]) -> ExtendedDict:
        """Return a deeply merged copy."""
        return ExtendedDict(deep_merge(self.data, *mappings))

    def flatten(self, *, separator: str = ".") -> ExtendedDict:
        """Return a flattened copy."""
        return ExtendedDict(flatten_map(self.data, separator=separator))

    def filter(
        self,
        *,
        allowlist: list[str] | None = None,
        denylist: list[str] | None = None,
    ) -> tuple[ExtendedDict, ExtendedDict]:
        """Return accepted and rejected mapping entries."""
        accepted, rejected = filter_map(self.data, allowlist=allowlist, denylist=denylist)
        return ExtendedDict(accepted), ExtendedDict(rejected)

    def compact(self) -> ExtendedDict:
        """Return a copy without values considered empty."""
        return ExtendedDict(all_non_empty_in_dict(self.data))

    def deduplicate(self) -> ExtendedDict:
        """Return a copy with nested duplicate list values removed."""
        return ExtendedDict(deduplicate_map(self.data))

    def unhump(self, *, drop_without_prefix: str | None = None) -> ExtendedDict:
        """Return a copy with camelCase keys converted to snake_case."""
        return ExtendedDict(unhump_map(self.data, drop_without_prefix=drop_without_prefix))

    def all_values(self) -> list[Any]:
        """Return all values from the nested mapping."""
        return all_values_from_map(self.data)

    def first_non_empty_value(self, *keys: str) -> Any:
        """Return the first non-empty value for the provided keys."""
        return first_non_empty_value_from_map(self.data, *keys)
