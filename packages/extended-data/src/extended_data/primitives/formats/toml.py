"""TOML Utilities Module.

This module provides utilities for encoding and decoding TOML data using tomlkit.
"""

from __future__ import annotations

from typing import Any

import tomlkit

from extended_data.primitives.formats._normalization import lower_extended_data
from extended_data.primitives.formats.errors import DataDecodeError, invalid_utf8_error
from extended_data.primitives.strings import bytes_to_string
from extended_data.primitives.types import convert_special_types


def decode_toml(toml_data: str | memoryview | bytes | bytearray) -> Any:
    """Decodes a TOML string into a Python object using tomlkit.

    Args:
        toml_data (str | memoryview | bytes | bytearray): The TOML string to decode.

    Returns:
        Any: The decoded Python object with any special types processed.
    """
    try:
        toml_data = bytes_to_string(toml_data)
    except UnicodeDecodeError as exc:
        raise invalid_utf8_error("TOML") from exc
    try:
        return tomlkit.parse(toml_data)
    except tomlkit.exceptions.TOMLKitError as exc:
        raise DataDecodeError.from_exception("TOML", exc) from exc


def encode_toml(raw_data: Any) -> str:
    """Encodes a Python object into a TOML string using tomlkit.

    Args:
        raw_data (Any): The Python object to encode.

    Returns:
        str: The encoded TOML string.
    """
    # Convert unsupported types to simpler forms before encoding
    converted_data = convert_special_types(lower_extended_data(raw_data))
    return tomlkit.dumps(converted_data)
