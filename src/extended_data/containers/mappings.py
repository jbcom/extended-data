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
        from extended_data.containers.factory import extend_data, to_builtin

        return extend_data(deep_merge(to_builtin(self.data), *(to_builtin(mapping) for mapping in mappings)))

    def flatten(self, *, separator: str = ".") -> ExtendedDict:
        """Return a flattened copy."""
        from extended_data.containers.factory import extend_data, to_builtin

        return extend_data(flatten_map(to_builtin(self.data), separator=separator))

    def filter(
        self,
        *,
        allowlist: list[str] | None = None,
        denylist: list[str] | None = None,
    ) -> tuple[ExtendedDict, ExtendedDict]:
        """Return accepted and rejected mapping entries."""
        from extended_data.containers.factory import extend_data, to_builtin

        accepted, rejected = filter_map(to_builtin(self.data), allowlist=allowlist, denylist=denylist)
        return extend_data(accepted), extend_data(rejected)

    def compact(self) -> ExtendedDict:
        """Return a copy without values considered empty."""
        from extended_data.containers.factory import extend_data, to_builtin

        return extend_data(all_non_empty_in_dict(to_builtin(self.data)))

    def deduplicate(self) -> ExtendedDict:
        """Return a copy with nested duplicate list values removed."""
        from extended_data.containers.factory import extend_data, to_builtin

        return extend_data(deduplicate_map(to_builtin(self.data)))

    def unhump(self, *, drop_without_prefix: str | None = None) -> ExtendedDict:
        """Return a copy with camelCase keys converted to snake_case."""
        from extended_data.containers.factory import extend_data, to_builtin

        return extend_data(unhump_map(to_builtin(self.data), drop_without_prefix=drop_without_prefix))

    def all_values(self) -> list[Any]:
        """Return all values from the nested mapping."""
        from extended_data.containers.factory import to_builtin

        return all_values_from_map(to_builtin(self.data))

    def first_non_empty_value(self, *keys: str) -> Any:
        """Return the first non-empty value for the provided keys."""
        from extended_data.containers.factory import to_builtin

        return first_non_empty_value_from_map(to_builtin(self.data), *keys)
