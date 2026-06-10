"""This module provides utility functions for YAML encoding and decoding.

It includes functions to decode YAML strings, encode Python objects to YAML,
and check if data is a YAML tagged object.
"""

from __future__ import annotations

from typing import Any

import yaml

from extended_data.primitives.formats._normalization import lower_extended_data
from extended_data.primitives.formats.errors import DataDecodeError, invalid_utf8_error
from extended_data.primitives.formats.yaml.dumpers import PureDumper
from extended_data.primitives.formats.yaml.loaders import PureLoader
from extended_data.primitives.formats.yaml.tag_classes import YamlPairs, YamlTagged
from extended_data.primitives.strings import bytestostr


def decode_yaml(yaml_data: str | memoryview | bytes | bytearray) -> Any:
    """Decode YAML data into a Python object.

    Args:
        yaml_data (str | memoryview | bytes | bytearray): The YAML data to decode.

    Returns:
        Any: The decoded Python object.
    """
    try:
        yaml_data = bytestostr(yaml_data)
    except UnicodeDecodeError as exc:
        raise invalid_utf8_error("YAML") from exc
    try:
        return yaml.load(yaml_data, Loader=PureLoader)  # noqa: S506
    except yaml.YAMLError as exc:
        raise DataDecodeError.from_exception("YAML", exc) from exc


def encode_yaml(raw_data: Any) -> str:
    """Encode a Python object into a YAML string.

    Args:
        raw_data (Any): The Python object to encode.

    Returns:
        str: The encoded YAML string.
    """
    return yaml.dump(lower_extended_data(raw_data), Dumper=PureDumper, allow_unicode=True, sort_keys=False)


def is_yaml_data(data: Any) -> bool:
    """Check if the data is a YAML tagged object.

    Args:
        data (Any): The data to check.

    Returns:
        bool: True if the data is a YAML tagged object, False otherwise.
    """
    if isinstance(data, (YamlTagged, YamlPairs)):
        return True
    if isinstance(data, dict):
        for value in data.values():
            if is_yaml_data(value):
                return True
    if isinstance(data, list):
        for item in data:
            if is_yaml_data(item):
                return True
    if isinstance(data, tuple):
        for item in data:
            if is_yaml_data(item):
                return True
    return False
