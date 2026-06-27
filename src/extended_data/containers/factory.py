"""Factories for moving between plain data and extended containers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from extended_data.containers.mappings import ExtendedDict
from extended_data.containers.sequences import ExtendedList, ExtendedSet, ExtendedTuple
from extended_data.containers.strings import ExtendedString
from extended_data.primitives.formats.yaml import LiteralScalarString, YamlPairs, YamlTagged


def extend_data(value: Any) -> Any:
    """Recursively wrap built-in containers in Extended Data containers."""
    from extended_data.containers.data import ExtendedData

    if isinstance(value, YamlTagged | YamlPairs | LiteralScalarString):
        return value
    if isinstance(value, ExtendedString | ExtendedDict | ExtendedList | ExtendedSet | ExtendedTuple):
        return value
    if isinstance(value, ExtendedData):
        return value
    if isinstance(value, str):
        return ExtendedString(value)
    if isinstance(value, Mapping):
        return ExtendedDict({key: extend_data(item) for key, item in value.items()})
    if isinstance(value, list):
        return ExtendedList(extend_data(item) for item in value)
    if isinstance(value, tuple):
        return ExtendedTuple(extend_data(item) for item in value)
    if isinstance(value, set | frozenset):
        return ExtendedSet(extend_data(item) for item in value)
    return value


def to_builtin(value: Any) -> Any:
    """Recursively unwrap Extended Data containers to built-in Python values."""
    from extended_data.containers.data import ExtendedData

    if isinstance(value, YamlTagged | YamlPairs | LiteralScalarString):
        return value
    if isinstance(value, ExtendedString):
        return str(value)
    if isinstance(value, ExtendedDict):
        return {to_builtin(key): to_builtin(item) for key, item in value.items()}
    if isinstance(value, ExtendedList):
        return [to_builtin(item) for item in value]
    if isinstance(value, ExtendedTuple):
        return tuple(to_builtin(item) for item in value)
    if isinstance(value, ExtendedSet):
        return {to_builtin(item) for item in value}
    if isinstance(value, ExtendedData):
        return to_builtin(value.value)
    if isinstance(value, Mapping):
        return {to_builtin(key): to_builtin(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_builtin(item) for item in value]
    if isinstance(value, tuple):
        return tuple(to_builtin(item) for item in value)
    if isinstance(value, set):
        return {to_builtin(item) for item in value}
    if isinstance(value, frozenset):
        return frozenset(to_builtin(item) for item in value)
    return value
