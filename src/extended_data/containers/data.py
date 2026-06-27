"""Generic Extended Data container facade."""

from __future__ import annotations

from collections import UserString
from collections.abc import Callable, Iterable, Iterator, Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any, Self

from extended_data.containers.mappings import ExtendedDict
from extended_data.containers.sequences import ExtendedList, ExtendedSet, ExtendedTuple
from extended_data.containers.strings import ExtendedString


class ExtendedData:
    """Stable holder for any promoted Extended Data value.

    ``extend_data`` returns the most specific Tier 2 container for a value. This
    facade is for higher-level code that cannot or should not care whether the
    current payload is mapping-, sequence-, string-, set-, scalar-, or object-
    shaped.
    """

    __hash__ = None  # type: ignore[assignment]

    def __init__(self, value: Any = None) -> None:
        """Promote and store any supported data shape."""
        from extended_data.containers.factory import extend_data

        self._value = value.value if isinstance(value, ExtendedData) else extend_data(value)

    @property
    def value(self) -> Any:
        """Return the promoted underlying value."""
        return self._value

    @property
    def data_type(self) -> str:
        """Return the promoted value type name."""
        return type(self._value).__name__

    @property
    def shape(self) -> str:
        """Return the broad data shape represented by the current value."""
        if self._value is None:
            return "none"
        if isinstance(self._value, ExtendedDict | Mapping):
            return "mapping"
        if isinstance(self._value, ExtendedList | list):
            return "list"
        if isinstance(self._value, ExtendedTuple | tuple):
            return "tuple"
        if isinstance(self._value, ExtendedSet | set | frozenset):
            return "set"
        if isinstance(self._value, ExtendedString | str | UserString):
            return "string"
        if isinstance(self._value, bool | int | float | complex | bytes | bytearray | memoryview | Path):
            return "scalar"
        return "object"

    @property
    def is_mapping(self) -> bool:
        """Return whether this value is mapping-shaped."""
        return self.shape == "mapping"

    @property
    def is_sequence(self) -> bool:
        """Return whether this value is list- or tuple-shaped."""
        return self.shape in {"list", "tuple"}

    @property
    def is_string(self) -> bool:
        """Return whether this value is string-shaped."""
        return self.shape == "string"

    @property
    def is_set(self) -> bool:
        """Return whether this value is set-shaped."""
        return self.shape == "set"

    @property
    def is_scalar(self) -> bool:
        """Return whether this value is scalar-shaped."""
        return self.shape == "scalar"

    @property
    def is_none(self) -> bool:
        """Return whether this value is ``None``."""
        return self.shape == "none"

    @classmethod
    def from_value(cls, value: Any = None) -> ExtendedData:
        """Create an ``ExtendedData`` wrapper from any value."""
        return cls(value)

    @classmethod
    def decode(
        cls,
        data: str | memoryview | bytes | bytearray,
        *,
        file_path: str | Path | None = None,
        suffix: str | None = None,
    ) -> ExtendedData:
        """Decode raw structured data and return a generic wrapper."""
        from extended_data.io.files import decode_file

        return cls(decode_file(data, file_path=file_path, suffix=suffix, as_extended=True))

    @classmethod
    def read(
        cls,
        file_path: str | Path,
        *,
        suffix: str | None = None,
        charset: str = "utf-8",
        errors: str = "strict",
        headers: Mapping[str, str] | None = None,
        tld: Path | None = None,
    ) -> ExtendedData:
        """Read a local file or URL and return decoded generic data."""
        from extended_data.io.files import read_data_file

        return cls(
            read_data_file(
                file_path,
                suffix=suffix,
                as_extended=True,
                charset=charset,
                errors=errors,
                headers=headers,
                tld=tld,
            )
        )

    def as_builtin(self) -> Any:
        """Return the value lowered to built-in Python containers."""
        from extended_data.containers.factory import to_builtin

        return to_builtin(self._value)

    def as_extended(self) -> Any:
        """Return a detached promoted copy of the value."""
        from extended_data.containers.factory import extend_data

        return extend_data(deepcopy(self.as_builtin()))

    def copy(self) -> ExtendedData:
        """Return a detached ``ExtendedData`` copy."""
        return ExtendedData(deepcopy(self._value))

    def replace(self, value: Any) -> Self:
        """Replace the underlying value and return this facade."""
        from extended_data.containers.factory import extend_data

        self._value = extend_data(value)
        return self

    def map(self, transform: Callable[[Any], Any]) -> ExtendedData:
        """Apply a callable to the promoted value and wrap the result."""
        return ExtendedData(transform(self._value))

    def map_builtin(self, transform: Callable[[Any], Any]) -> ExtendedData:
        """Apply a callable to lowered built-in data and wrap the result."""
        return ExtendedData(transform(self.as_builtin()))

    def transform(self, *steps: str) -> ExtendedData:
        """Apply named DataWorkflow transforms and wrap the result."""
        from extended_data.workflows import DataWorkflow

        return ExtendedData(DataWorkflow.from_value(self._value).transform(*steps).result().value)

    def merge(self, *mappings: Mapping[str, Any]) -> ExtendedData:
        """Deep-merge mappings when this wrapper contains mapping-shaped data."""
        method = getattr(self._value, "deep_merge", None)
        if not callable(method):
            raise TypeError(f"merge is not available for {self.data_type}")
        return ExtendedData(method(*mappings))

    def workflow(self) -> Any:
        """Start a DataWorkflow from this value."""
        from extended_data.workflows import DataWorkflow

        return DataWorkflow.from_value(self._value)

    def sync_to_file(
        self,
        file_path: str | Path,
        *,
        source: str = "memory",
        encoding: str | None = None,
        charset: str = "utf-8",
        allow_empty: bool = False,
        dry_run: bool = False,
        tld: Path | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> Any:
        """Sync this value to a local file through the shared data sync primitive."""
        from extended_data.workflows.sync import sync_value_to_file

        return sync_value_to_file(
            self.as_builtin(),
            file_path,
            source=source,
            encoding=encoding,
            charset=charset,
            allow_empty=allow_empty,
            dry_run=dry_run,
            tld=tld,
            metadata=metadata,
        )

    def write(
        self,
        file_path: str | Path,
        *,
        encoding: str | None = None,
        charset: str = "utf-8",
        allow_empty: bool = False,
        tld: Path | None = None,
    ) -> Path | None:
        """Write this value to a file and return the output path."""
        from extended_data.io.files import write_file

        return write_file(
            file_path,
            self.as_builtin(),
            encoding=encoding,
            charset=charset,
            allow_empty=allow_empty,
            tld=tld,
        )

    def to_export_safe(self, *, export_to_yaml: bool = False) -> Any:
        """Return this value converted to export-safe primitive data."""
        from extended_data.io.exporters import make_raw_data_export_safe

        return make_raw_data_export_safe(self._value, export_to_yaml=export_to_yaml)

    def wrap_for_export(self, allow_encoding: bool | str = True, **format_opts: Any) -> str:
        """Return this value wrapped as an encoded export string."""
        from extended_data.io.exporters import wrap_raw_data_for_export

        return wrap_raw_data_for_export(self._value, allow_encoding=allow_encoding, **format_opts)

    def get(self, key: Any, default: Any = None) -> Any:
        """Return a mapping value by key, or ``default`` when unavailable."""
        method = getattr(self._value, "get", None)
        if not callable(method):
            return default
        return method(key, default)

    def append(self, item: Any) -> Self:
        """Append to list-shaped data and return this wrapper."""
        method = getattr(self._value, "append", None)
        if not callable(method):
            raise TypeError(f"append is not available for {self.data_type}")
        method(item)
        return self

    def extend(self, values: Iterable[Any]) -> Self:
        """Extend list-shaped data and return this wrapper."""
        method = getattr(self._value, "extend", None)
        if not callable(method):
            raise TypeError(f"extend is not available for {self.data_type}")
        method(values)
        return self

    def update(self, *args: Any, **kwargs: Any) -> Self:
        """Update mapping- or set-shaped data and return this wrapper."""
        method = getattr(self._value, "update", None)
        if not callable(method):
            raise TypeError(f"update is not available for {self.data_type}")
        method(*args, **kwargs)
        return self

    def add(self, item: Any) -> Self:
        """Add to set-shaped data and return this wrapper."""
        method = getattr(self._value, "add", None)
        if not callable(method):
            raise TypeError(f"add is not available for {self.data_type}")
        method(item)
        return self

    def __getattr__(self, name: str) -> Any:
        """Delegate shape-specific operations to the promoted value."""
        try:
            value = object.__getattribute__(self, "_value")
        except AttributeError as exc:
            raise AttributeError(name) from exc
        return getattr(value, name)

    def __iter__(self) -> Iterator[Any]:
        """Iterate the underlying value."""
        try:
            return iter(self._value)
        except TypeError:
            return iter([self._value])

    def __len__(self) -> int:
        """Return the underlying value length, or one for scalars."""
        try:
            return len(self._value)
        except TypeError:
            return 1

    def __bool__(self) -> bool:
        """Mirror the truthiness of the wrapped value."""
        return bool(self._value)

    def __getitem__(self, key: Any) -> Any:
        """Index the underlying value."""
        return self._value[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        """Set an item on mutable underlying data."""
        self._value[key] = value

    def __delitem__(self, key: Any) -> None:
        """Delete an item from mutable underlying data."""
        del self._value[key]

    def __contains__(self, item: object) -> bool:
        """Return whether an item is present in the underlying value."""
        try:
            return item in self._value
        except TypeError:
            return False

    def __eq__(self, other: object) -> bool:
        """Compare against another facade or raw value by built-in representation."""
        if isinstance(other, ExtendedData):
            return self.as_builtin() == other.as_builtin()
        return self.as_builtin() == other

    def __repr__(self) -> str:
        """Return a useful debugging representation."""
        return f"ExtendedData({self._value!r})"
