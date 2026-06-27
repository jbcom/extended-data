"""Generic Extended Data container facade."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any, Self


class ExtendedData:
    """Generic wrapper for any promoted Extended Data value."""

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

    def as_builtin(self) -> Any:
        """Return the value lowered to built-in Python containers."""
        from extended_data.containers.factory import to_builtin

        return to_builtin(self._value)

    def as_extended(self) -> Any:
        """Return a detached promoted copy of the value."""
        from extended_data.containers.factory import extend_data

        return extend_data(deepcopy(self.as_builtin()))

    def replace(self, value: Any) -> Self:
        """Replace the underlying value and return this facade."""
        from extended_data.containers.factory import extend_data

        self._value = extend_data(value)
        return self

    def map(self, transform: Any) -> ExtendedData:
        """Apply a callable to the promoted value and wrap the result."""
        return ExtendedData(transform(self._value))

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

    def to_export_safe(self, *, export_to_yaml: bool = False) -> Any:
        """Return this value converted to export-safe primitive data."""
        from extended_data.io.exporters import make_raw_data_export_safe

        return make_raw_data_export_safe(self._value, export_to_yaml=export_to_yaml)

    def wrap_for_export(self, allow_encoding: bool | str = True, **format_opts: Any) -> str:
        """Return this value wrapped as an encoded export string."""
        from extended_data.io.exporters import wrap_raw_data_for_export

        return wrap_raw_data_for_export(self._value, allow_encoding=allow_encoding, **format_opts)

    def __getattr__(self, name: str) -> Any:
        """Delegate shape-specific operations to the promoted value."""
        return getattr(self._value, name)

    def __iter__(self) -> Any:
        """Iterate the underlying value."""
        return iter(self._value)

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

    def __eq__(self, other: object) -> bool:
        """Compare against another facade or raw value by built-in representation."""
        if isinstance(other, ExtendedData):
            return self.as_builtin() == other.as_builtin()
        return self.as_builtin() == other

    def __repr__(self) -> str:
        """Return a useful debugging representation."""
        return f"ExtendedData({self._value!r})"
