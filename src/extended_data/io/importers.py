"""This module provides utilities for unwrapping data after import."""

from __future__ import annotations

from typing import Any

from extended_data.primitives.formats.hcl import decode_hcl2
from extended_data.primitives.formats.json import decode_json
from extended_data.primitives.formats.toml import decode_toml
from extended_data.primitives.formats.yaml import decode_yaml
from extended_data.primitives.serialization import normalize_data_encoding
from extended_data.primitives.strings import bytestostr


def unwrap_raw_data_from_import(
    wrapped_data: str | memoryview | bytes | bytearray,
    encoding: str = "yaml",
) -> Any:
    """Unwraps the data that was wrapped for import.

    Args:
        wrapped_data (str | memoryview | bytes | bytearray): The wrapped data.
        encoding (str): The encoding format (default is 'yaml').

    Returns:
        Any: The unwrapped data.

    Raises:
        ValueError: If the encoding format is unsupported.
    """
    normalized_encoding = normalize_data_encoding(encoding)

    if normalized_encoding == "yaml":
        return decode_yaml(wrapped_data)
    if normalized_encoding == "json":
        return decode_json(wrapped_data)
    if normalized_encoding == "toml":
        return decode_toml(wrapped_data)
    if normalized_encoding == "hcl":
        return decode_hcl2(wrapped_data)
    if normalized_encoding == "raw":
        return bytestostr(wrapped_data)

    error_message = f"Unsupported encoding format: {encoding}"
    raise ValueError(error_message)
