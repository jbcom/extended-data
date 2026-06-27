"""Generic Extended Data root and factory."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any, Self, cast


class ExtendedData:
    """Common root and factory for any Extended Data value.

    ``ExtendedData(value)`` returns the most specific concrete Tier 2 container
    whenever one exists. Mapping values become ``ExtendedDict`` instances, list
    values become ``ExtendedList`` instances, strings become ``ExtendedString``
    instances, and so on. Scalars and arbitrary objects remain in a small generic
    holder so the same workflow, export, and sync helpers are available at file,
    API, and vendor boundaries.
    """

    def __new__(cls, value: Any = None) -> Self:
        """Return the most specific Extended Data object for ``value``."""
        if cls is not ExtendedData:
            return super().__new__(cls)

        from extended_data.containers.factory import extend_data

        promoted = extend_data(value)
        if isinstance(promoted, ExtendedData):
            return cast(Self, promoted)

        instance = super().__new__(cls)
        instance._value = promoted
        return instance

    def __init__(self, value: Any = None) -> None:
        """Initialize scalar/object holders without touching concrete subtypes."""
        if type(self) is ExtendedData and not hasattr(self, "_value"):
            self._value = value

    @property
    def value(self) -> Any:
        """Return the concrete value represented by this object."""
        if type(self) is ExtendedData:
            return self._value
        return self

    @property
    def data_type(self) -> str:
        """Return this value type name."""
        return type(self.value).__name__

    @property
    def shape(self) -> str:
        """Return the broad data shape represented by this value."""
        from collections import UserString

        from extended_data.containers.mappings import ExtendedDict
        from extended_data.containers.sequences import ExtendedList, ExtendedSet, ExtendedTuple
        from extended_data.containers.strings import ExtendedString

        value = self.value
        if value is None:
            return "none"
        if isinstance(value, ExtendedDict | Mapping):
            return "mapping"
        if isinstance(value, ExtendedList | list):
            return "list"
        if isinstance(value, ExtendedTuple | tuple):
            return "tuple"
        if isinstance(value, ExtendedSet | set | frozenset):
            return "set"
        if isinstance(value, ExtendedString | str | UserString):
            return "string"
        if isinstance(value, bool | int | float | complex | bytes | bytearray | memoryview | Path):
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
        """Create an Extended Data object from any value."""
        return cls(value)

    @classmethod
    def decode(
        cls,
        data: str | memoryview | bytes | bytearray,
        *,
        file_path: str | Path | None = None,
        suffix: str | None = None,
    ) -> ExtendedData:
        """Decode raw structured data and return concrete Extended Data."""
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
        """Read a local file or URL and return concrete Extended Data."""
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

        return to_builtin(self.value)

    def as_extended(self) -> Any:
        """Return a detached promoted copy of the value."""
        from extended_data.containers.factory import extend_data

        return extend_data(deepcopy(self.as_builtin()))

    def copy(self) -> ExtendedData:
        """Return a detached Extended Data copy."""
        return ExtendedData(deepcopy(self.as_builtin()))

    def cast(self, value: Any) -> ExtendedData:
        """Return ``value`` promoted into the appropriate Extended Data subtype."""
        return ExtendedData(value)

    def map(self, transform: Callable[[Any], Any]) -> ExtendedData:
        """Apply a callable to this value and wrap the result."""
        return ExtendedData(transform(self.value))

    def map_builtin(self, transform: Callable[[Any], Any]) -> ExtendedData:
        """Apply a callable to lowered built-in data and wrap the result."""
        return ExtendedData(transform(self.as_builtin()))

    def transform(self, *steps: str) -> ExtendedData:
        """Apply named DataWorkflow transforms and wrap the result."""
        from extended_data.workflows import DataWorkflow

        return ExtendedData(DataWorkflow.from_value(self.value).transform(*steps).result().value)

    def merge(self, *mappings: Mapping[str, Any]) -> ExtendedData:
        """Deep-merge mappings when this wrapper contains mapping-shaped data."""
        method = getattr(self.value, "deep_merge", None)
        if not callable(method):
            raise TypeError(f"merge is not available for {self.data_type}")
        return ExtendedData(method(*mappings))

    def workflow(self) -> Any:
        """Start a DataWorkflow from this value."""
        from extended_data.workflows import DataWorkflow

        return DataWorkflow.from_value(self.value)

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

        return make_raw_data_export_safe(self.value, export_to_yaml=export_to_yaml)

    def wrap_for_export(self, allow_encoding: bool | str = True, **format_opts: Any) -> str:
        """Return this value wrapped as an encoded export string."""
        from extended_data.io.exporters import wrap_raw_data_for_export

        return wrap_raw_data_for_export(self.value, allow_encoding=allow_encoding, **format_opts)

    def get(self, key: Any, default: Any = None) -> Any:
        """Return a mapping value by key, or ``default`` when unavailable."""
        if not self.is_mapping:
            return default
        try:
            return self[key]
        except KeyError:
            return default

    def append(self, item: Any) -> Self:
        """Append to list-shaped data and return this wrapper."""
        value = self.value
        if value is self:
            raise TypeError(f"append is not available for {self.data_type}")
        method = getattr(value, "append", None)
        if not callable(method):
            raise TypeError(f"append is not available for {self.data_type}")
        method(item)
        return self

    def extend(self, values: Iterable[Any]) -> Self:
        """Extend list-shaped data and return this wrapper."""
        value = self.value
        if value is self:
            raise TypeError(f"extend is not available for {self.data_type}")
        method = getattr(value, "extend", None)
        if not callable(method):
            raise TypeError(f"extend is not available for {self.data_type}")
        method(values)
        return self

    def update(self, *args: Any, **kwargs: Any) -> Self:
        """Update mapping- or set-shaped data and return this wrapper."""
        value = self.value
        if value is self:
            raise TypeError(f"update is not available for {self.data_type}")
        method = getattr(value, "update", None)
        if not callable(method):
            raise TypeError(f"update is not available for {self.data_type}")
        method(*args, **kwargs)
        return self

    def add(self, item: Any) -> Self:
        """Add to set-shaped data and return this wrapper."""
        value = self.value
        if value is self:
            raise TypeError(f"add is not available for {self.data_type}")
        method = getattr(value, "add", None)
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
        value = self.value
        if value is self:
            msg = f"iteration is not available for {self.data_type}"
            raise TypeError(msg)
        try:
            return iter(value)
        except TypeError:
            return iter([value])

    def __len__(self) -> int:
        """Return the underlying value length, or one for scalars."""
        value = self.value
        if value is self:
            msg = f"length is not available for {self.data_type}"
            raise TypeError(msg)
        try:
            return len(value)
        except TypeError:
            return 1

    def __bool__(self) -> bool:
        """Mirror the truthiness of the wrapped value."""
        value = self.value
        if value is self:
            return len(self) > 0
        return bool(value)

    def __getitem__(self, key: Any) -> Any:
        """Index the underlying value."""
        value = self.value
        if value is self:
            msg = f"indexing is not available for {self.data_type}"
            raise TypeError(msg)
        return value[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        """Set an item on mutable underlying data."""
        target = self.value
        if target is self:
            msg = f"item assignment is not available for {self.data_type}"
            raise TypeError(msg)
        target[key] = value

    def __delitem__(self, key: Any) -> None:
        """Delete an item from mutable underlying data."""
        value = self.value
        if value is self:
            msg = f"item deletion is not available for {self.data_type}"
            raise TypeError(msg)
        del value[key]

    def __contains__(self, item: object) -> bool:
        """Return whether an item is present in the underlying value."""
        value = self.value
        if value is self:
            try:
                self[item]
            except (IndexError, KeyError, TypeError):
                return False
            return True
        try:
            return item in value
        except TypeError:
            return False

    def __repr__(self) -> str:
        """Return a useful debugging representation."""
        return f"ExtendedData({self.value!r})"
