"""Extended mapping container built on Tier 1 primitives."""

from __future__ import annotations

from collections import UserDict
from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING, Any, overload

from typing_extensions import Self


if TYPE_CHECKING:
    from _typeshed import SupportsKeysAndGetItem

    from extended_data.containers.sequences import ExtendedList, ExtendedTuple

from extended_data.primitives.mappings import (
    all_values_from_map,
    deduplicate_map,
    deep_merge,
    filter_map,
    first_non_empty_value_from_map,
    flatten_map,
    unhump_map,
)
from extended_data.primitives.splitting import split_dict_by_type
from extended_data.primitives.state import all_non_empty_in_dict, any_non_empty, yield_non_empty
from extended_data.primitives.types import reconstruct_special_types


class ExtendedDict(UserDict[str, Any]):
    """Dictionary wrapper with chainable primitive operations."""

    def __init__(self, initialdata: Mapping[str, Any] | None = None, **kwargs: Any) -> None:
        """Initialize the extended dictionary."""
        super().__init__()
        self.update(initialdata or {}, **kwargs)

    def __setitem__(self, key: str, item: Any) -> None:
        """Set a value while preserving extended nested containers."""
        from extended_data.containers.factory import extend_data

        self.data[key] = extend_data(item)

    @overload
    def update(self, other: SupportsKeysAndGetItem[str, Any], /) -> None: ...

    @overload
    def update(self, other: SupportsKeysAndGetItem[str, Any], /, **kwargs: Any) -> None: ...

    @overload
    def update(self, other: Iterable[tuple[str, Any]], /) -> None: ...

    @overload
    def update(self, other: Iterable[tuple[str, Any]], /, **kwargs: Any) -> None: ...

    @overload
    def update(self, **kwargs: Any) -> None: ...

    def update(self, *args: Any, **kwargs: Any) -> None:  # type: ignore[misc]
        """Update values while preserving extended nested containers."""
        if len(args) > 1:
            msg = f"update expected at most 1 argument, got {len(args)}"
            raise TypeError(msg)

        if args:
            other = args[0]
            items = other.items() if hasattr(other, "items") else other
            for key, value in items:
                self[key] = value

        for key, value in kwargs.items():
            self[key] = value

    def setdefault(self, key: str, default: Any = None) -> Any:
        """Insert a default while returning the promoted stored value."""
        if key not in self.data:
            self[key] = default
        return self.data[key]

    def __ior__(self, other: Any) -> Self:  # type: ignore[override,misc]
        """Update from a mapping or item iterable while preserving extended containers."""
        self.update(other)
        return self

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
    ) -> ExtendedTuple[ExtendedDict]:
        """Return accepted and rejected mapping entries."""
        from extended_data.containers.factory import extend_data, to_builtin
        from extended_data.containers.sequences import ExtendedTuple

        accepted, rejected = filter_map(to_builtin(self.data), allowlist=allowlist, denylist=denylist)
        return ExtendedTuple((extend_data(accepted), extend_data(rejected)))

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

    def all_values(self) -> ExtendedList[Any]:
        """Return all values from the nested mapping."""
        from extended_data.containers.factory import extend_data, to_builtin

        return extend_data(all_values_from_map(to_builtin(self.data)))

    def split_by_type(self, *, primitive_only: bool = False) -> ExtendedDict:
        """Return mapping entries grouped by value type name."""
        from extended_data.containers.factory import extend_data, to_builtin

        grouped = split_dict_by_type(to_builtin(self.data), primitive_only=primitive_only)
        return extend_data({type_key.__name__: values for type_key, values in grouped.items()})

    def first_non_empty_value(self, *keys: str) -> Any:
        """Return the first non-empty value for the provided keys."""
        from extended_data.containers.factory import extend_data, to_builtin

        return extend_data(first_non_empty_value_from_map(to_builtin(self.data), *keys))

    def first_non_empty_entry(self, *keys: str) -> ExtendedDict:
        """Return the first non-empty keyed entry for the provided keys."""
        from extended_data.containers.factory import extend_data, to_builtin

        return extend_data(any_non_empty(to_builtin(self.data), *keys))

    def non_empty_entries(self, *keys: str) -> ExtendedList[ExtendedDict]:
        """Return all non-empty keyed entries for the provided keys."""
        from extended_data.containers.factory import extend_data, to_builtin

        return extend_data(list(yield_non_empty(to_builtin(self.data), *keys)))

    def reconstruct_special_types(self, *, fail_silently: bool = False) -> ExtendedDict:
        """Return a copy with string-like special values reconstructed."""
        from extended_data.containers.factory import extend_data, to_builtin

        return extend_data(reconstruct_special_types(to_builtin(self.data), fail_silently=fail_silently))

    def to_export_safe(self, *, export_to_yaml: bool = False) -> Any:
        """Return this mapping converted to export-safe primitive data."""
        from extended_data.io.exporters import make_raw_data_export_safe

        return make_raw_data_export_safe(self.data, export_to_yaml=export_to_yaml)

    def wrap_for_export(self, allow_encoding: bool | str = True, **format_opts: Any) -> str:
        """Return this mapping wrapped as an encoded export string."""
        from extended_data.io.exporters import wrap_raw_data_for_export

        return wrap_raw_data_for_export(self.data, allow_encoding=allow_encoding, **format_opts)
