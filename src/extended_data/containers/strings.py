"""Extended string container built on Tier 1 primitives."""

from __future__ import annotations

from collections import UserString
from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING

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
    removeprefix,
    removesuffix,
    sanitize_key,
    titleize_name,
    truncate,
    upper_first_char,
)
from extended_data.primitives.types import strtobool


if TYPE_CHECKING:
    from extended_data.containers.sequences import ExtendedList, ExtendedTuple


def _coerce_string_argument(value: str | UserString) -> str:
    """Coerce stdlib user strings while preserving normal str errors elsewhere."""
    return str(value) if isinstance(value, UserString) else value


class ExtendedString(UserString):
    """String wrapper with chainable primitive operations."""

    def lower_first(self) -> ExtendedString:
        """Return a copy with the first character lowercased."""
        return ExtendedString(lower_first_char(self.data))

    def upper_first(self) -> ExtendedString:
        """Return a copy with the first character uppercased."""
        return ExtendedString(upper_first_char(self.data))

    def remove_prefix(self, prefix: str) -> ExtendedString:
        """Return a copy with a leading prefix removed."""
        return ExtendedString(removeprefix(self.data, prefix))

    def remove_suffix(self, suffix: str) -> ExtendedString:
        """Return a copy with a trailing suffix removed."""
        return ExtendedString(removesuffix(self.data, suffix))

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

    def is_url(self) -> bool:
        """Return whether the string is a URL."""
        return is_url(self.data)

    def to_bool(self, *, raise_on_error: bool = False) -> bool | None:
        """Return a boolean parsed from the string."""
        return strtobool(self.data, raise_on_error=raise_on_error)
