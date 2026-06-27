"""Extended string container built on Tier 1 primitives."""

from __future__ import annotations

import datetime

from collections import UserString
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any

import extended_data.primitives.matching as primitive_matching

from extended_data.containers.data import _FACTORY_INITIALIZED_ATTR, ExtendedData
from extended_data.primitives.string_transforms import (
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
from extended_data.primitives.strings import (
    is_url,
    lower_first_char,
    sanitize_key,
    titleize_name,
    truncate,
    upper_first_char,
)
from extended_data.primitives.types import (
    reconstruct_special_type,
    string_to_bool,
    string_to_date,
    string_to_datetime,
    string_to_float,
    string_to_int,
    string_to_path,
    string_to_time,
)


if TYPE_CHECKING:
    from extended_data.containers.sequences import ExtendedList, ExtendedTuple


def _coerce_string_argument(value: str | UserString) -> str:
    """Coerce stdlib user strings while preserving normal str errors elsewhere."""
    return str(value) if isinstance(value, UserString) else value


class ExtendedString(UserString, ExtendedData):
    """String wrapper with chainable primitive operations."""

    def __init__(self, seq: object = "") -> None:
        """Initialize the extended string."""
        if getattr(self, _FACTORY_INITIALIZED_ATTR, False):
            setattr(self, _FACTORY_INITIALIZED_ATTR, False)
            return
        if seq is self:
            return
        super().__init__(seq)

    def lower_first(self) -> ExtendedString:
        """Return a copy with the first character lowercased."""
        return ExtendedString(lower_first_char(self.data))

    def upper_first(self) -> ExtendedString:
        """Return a copy with the first character uppercased."""
        return ExtendedString(upper_first_char(self.data))

    def remove_prefix(self, prefix: str) -> ExtendedString:
        """Return a copy with a leading prefix removed."""
        return ExtendedString(self.data.removeprefix(str(prefix)))

    def remove_suffix(self, suffix: str) -> ExtendedString:
        """Return a copy with a trailing suffix removed."""
        return ExtendedString(self.data.removesuffix(str(suffix)))

    def sanitize(self, delim: str = "_") -> ExtendedString:
        """Return a key-safe copy."""
        return ExtendedString(sanitize_key(self.data, delim=delim))

    def truncate(self, max_length: int, ender: str = "...") -> ExtendedString:
        """Return a truncated copy."""
        return ExtendedString(truncate(self.data, max_length=max_length, ender=ender))

    def titleize_name(self) -> ExtendedString:
        """Return a titleized name copy."""
        return ExtendedString(titleize_name(self.data))

    def to_snake_case(self) -> ExtendedString:
        """Return a snake_case copy."""
        return ExtendedString(to_snake_case(self.data))

    def to_camel_case(self, *, uppercase_first: bool = False) -> ExtendedString:
        """Return a camelCase copy."""
        return ExtendedString(to_camel_case(self.data, uppercase_first=uppercase_first))

    def to_pascal_case(self) -> ExtendedString:
        """Return a PascalCase copy."""
        return ExtendedString(to_pascal_case(self.data))

    def to_kebab_case(self) -> ExtendedString:
        """Return a kebab-case copy."""
        return ExtendedString(to_kebab_case(self.data))

    def pluralize(self) -> ExtendedString:
        """Return a pluralized copy."""
        return ExtendedString(pluralize(self.data))

    def singularize(self) -> ExtendedString:
        """Return a singularized copy."""
        return ExtendedString(singularize(self.data))

    def humanize(self) -> ExtendedString:
        """Return a human-readable copy."""
        return ExtendedString(humanize(self.data))

    def titleize(self) -> ExtendedString:
        """Return a title-case copy."""
        return ExtendedString(titleize(self.data))

    def ordinalize(self) -> ExtendedString:
        """Return an ordinalized copy."""
        return ExtendedString(ordinalize(self.data))

    def format(self, *args: object, **kwargs: object) -> ExtendedString:  # type: ignore[override]
        """Format values into an extended string."""
        return ExtendedString(self.data.format(*args, **kwargs))

    def format_map(self, mapping: Mapping[str, object]) -> ExtendedString:  # type: ignore[override]
        """Format mapping values into an extended string."""
        return ExtendedString(self.data.format_map(mapping))

    def split(self, sep: str | UserString | None = None, maxsplit: int = -1) -> ExtendedList[ExtendedString]:  # type: ignore[override]
        """Split into extended string parts."""
        from extended_data.containers.sequences import ExtendedList

        separator = None if sep is None else _coerce_string_argument(sep)
        return ExtendedList(ExtendedString(part) for part in self.data.split(separator, maxsplit))

    def rsplit(self, sep: str | UserString | None = None, maxsplit: int = -1) -> ExtendedList[ExtendedString]:  # type: ignore[override]
        """Split from the right into extended string parts."""
        from extended_data.containers.sequences import ExtendedList

        separator = None if sep is None else _coerce_string_argument(sep)
        return ExtendedList(ExtendedString(part) for part in self.data.rsplit(separator, maxsplit))

    def splitlines(self, keepends: bool = False) -> ExtendedList[ExtendedString]:  # type: ignore[override]
        """Split lines into extended string parts."""
        from extended_data.containers.sequences import ExtendedList

        return ExtendedList(ExtendedString(part) for part in self.data.splitlines(keepends))

    def partition(self, sep: str | UserString) -> ExtendedTuple[ExtendedString]:  # type: ignore[override]
        """Partition into extended string parts."""
        from extended_data.containers.sequences import ExtendedTuple

        return ExtendedTuple(ExtendedString(part) for part in self.data.partition(_coerce_string_argument(sep)))

    def rpartition(self, sep: str | UserString) -> ExtendedTuple[ExtendedString]:  # type: ignore[override]
        """Partition from the right into extended string parts."""
        from extended_data.containers.sequences import ExtendedTuple

        return ExtendedTuple(ExtendedString(part) for part in self.data.rpartition(_coerce_string_argument(sep)))

    def join(self, seq: Iterable[str | UserString]) -> ExtendedString:  # type: ignore[override]
        """Join string-like values into an extended string."""
        return ExtendedString(self.data.join(_coerce_string_argument(item) for item in seq))

    def is_partial_match(self, other: str | None, *, check_prefix_only: bool = False) -> bool:
        """Return whether this string partially matches another string."""
        return primitive_matching.is_partial_match(self.data, other, check_prefix_only=check_prefix_only)

    def is_non_empty_match(self, other: object) -> bool:
        """Return whether this string matches another non-empty string value."""
        return primitive_matching.is_non_empty_match(self.data, other)

    def is_url(self) -> bool:
        """Return whether the string is a URL."""
        return is_url(self.data)

    def to_bool(self, *, raise_on_error: bool = False) -> bool | None:
        """Return a boolean parsed from the string."""
        return string_to_bool(self.data, raise_on_error=raise_on_error)

    def to_float(self, *, raise_on_error: bool = False) -> float | None:
        """Return a float parsed from the string."""
        return string_to_float(self.data, raise_on_error=raise_on_error)

    def to_int(self, *, raise_on_error: bool = False) -> int | None:
        """Return an integer parsed from the string."""
        return string_to_int(self.data, raise_on_error=raise_on_error)

    def to_path(self, *, raise_on_error: bool = False) -> Path | None:
        """Return a path parsed from the string."""
        return string_to_path(self.data, raise_on_error=raise_on_error)

    def to_date(self, *, raise_on_error: bool = False) -> datetime.date | None:
        """Return a date parsed from the string."""
        return string_to_date(self.data, raise_on_error=raise_on_error)

    def to_datetime(self, *, raise_on_error: bool = False) -> datetime.datetime | None:
        """Return a datetime parsed from the string."""
        return string_to_datetime(self.data, raise_on_error=raise_on_error)

    def to_time(self, *, raise_on_error: bool = False) -> datetime.time | None:
        """Return a time parsed from the string."""
        return string_to_time(self.data, raise_on_error=raise_on_error)

    def reconstruct_special_type(self, *, fail_silently: bool = False) -> object:
        """Return the string reconstructed as a known scalar or structured value."""
        from extended_data.containers.factory import extend_data

        return extend_data(reconstruct_special_type(self.data, fail_silently=fail_silently))

    def decode_json(self, *, as_extended: bool = True) -> Any:
        """Decode this JSON string, promoting structured values by default."""
        from extended_data.containers.factory import extend_data
        from extended_data.primitives.formats.json import decode_json

        decoded = decode_json(self.data)
        return extend_data(decoded) if as_extended else decoded

    def decode_yaml(self, *, as_extended: bool = True) -> Any:
        """Decode this YAML string, promoting structured values by default."""
        from extended_data.containers.factory import extend_data
        from extended_data.primitives.formats.yaml import decode_yaml

        decoded = decode_yaml(self.data)
        return extend_data(decoded) if as_extended else decoded

    def decode_toml(self, *, as_extended: bool = True) -> Any:
        """Decode this TOML string, promoting structured values by default."""
        from extended_data.containers.factory import extend_data
        from extended_data.primitives.formats.toml import decode_toml

        decoded = decode_toml(self.data)
        return extend_data(decoded) if as_extended else decoded

    def decode_hcl2(self, *, as_extended: bool = True) -> Any:
        """Decode this HCL2 string, promoting structured values by default."""
        from extended_data.containers.factory import extend_data
        from extended_data.primitives.formats.hcl import decode_hcl2

        decoded = decode_hcl2(self.data)
        return extend_data(decoded) if as_extended else decoded

    def encode_base64(self, *, wrap_raw_data: bool = True) -> ExtendedString:
        """Return this string encoded as Base64."""
        from extended_data.io.base64 import base64_encode

        return ExtendedString(base64_encode(self.data, wrap_raw_data=wrap_raw_data))

    def decode_base64(
        self,
        unwrap_raw_data: bool = True,
        encoding: str = "yaml",
        *,
        as_extended: bool = True,
    ) -> Any:
        """Decode this Base64 string, promoting structured values by default."""
        from extended_data.io.base64 import base64_decode

        return base64_decode(
            self.data,
            unwrap_raw_data=unwrap_raw_data,
            encoding=encoding,
            as_extended=as_extended,
        )

    def to_export_safe(self, *, export_to_yaml: bool = False) -> Any:
        """Return this value converted to export-safe primitive data."""
        from extended_data.io.exporters import make_raw_data_export_safe

        return make_raw_data_export_safe(self.data, export_to_yaml=export_to_yaml)

    def wrap_for_export(self, allow_encoding: bool | str = True, **format_opts: Any) -> str:
        """Return this value wrapped as an encoded export string."""
        from extended_data.io.exporters import wrap_raw_data_for_export

        return wrap_raw_data_for_export(self.data, allow_encoding=allow_encoding, **format_opts)
