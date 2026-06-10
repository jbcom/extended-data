"""Factories for moving between plain data and extended containers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from extended_data.containers.mappings import ExtendedDict
from extended_data.containers.sequences import ExtendedList, ExtendedSet
from extended_data.containers.strings import ExtendedString
from extended_data.primitives.formats.yaml import LiteralScalarString, YamlPairs, YamlTagged


def extend_data(value: Any) -> Any:
    """Recursively wrap built-in containers in Extended Data containers."""
    if isinstance(value, YamlTagged | YamlPairs | LiteralScalarString):
        return value
    if isinstance(value, ExtendedString | ExtendedDict | ExtendedList | ExtendedSet):
        return value
    if isinstance(value, str):
        return ExtendedString(value)
    if isinstance(value, Mapping):
        return ExtendedDict({key: extend_data(item) for key, item in value.items()})
    if isinstance(value, list | tuple):
        return ExtendedList(extend_data(item) for item in value)
    if isinstance(value, set | frozenset):
        return ExtendedSet(extend_data(item) for item in value)
    return value


def to_builtin(value: Any) -> Any:
    """Recursively unwrap Extended Data containers to built-in Python values."""
    if isinstance(value, YamlTagged | YamlPairs | LiteralScalarString):
        return value
    if isinstance(value, ExtendedString):
        return str(value)
    if isinstance(value, ExtendedDict):
        return {key: to_builtin(item) for key, item in value.items()}
    if isinstance(value, ExtendedList):
        return [to_builtin(item) for item in value]
    if isinstance(value, ExtendedSet):
        return {to_builtin(item) for item in value}
    if isinstance(value, Mapping):
        return {key: to_builtin(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_builtin(item) for item in value]
    if isinstance(value, tuple):
        return tuple(to_builtin(item) for item in value)
    if isinstance(value, set):
        return {to_builtin(item) for item in value}
    if isinstance(value, frozenset):
        return frozenset(to_builtin(item) for item in value)
    return value
