"""This module provides utilities for unwrapping data after import."""

from __future__ import annotations

from typing import Any

from extended_data.containers.factory import extend_data
from extended_data.primitives.formats.hcl import decode_hcl2
from extended_data.primitives.formats.json import decode_json
from extended_data.primitives.formats.toml import decode_toml
from extended_data.primitives.formats.yaml import decode_yaml
from extended_data.primitives.serialization import normalize_data_encoding
from extended_data.primitives.strings import bytes_to_string


def unwrap_raw_data_from_import(
    wrapped_data: str | memoryview | bytes | bytearray,
    encoding: str = "yaml",
    *,
    as_extended: bool = True,
) -> Any:
    """Unwraps the data that was wrapped for import.

    Args:
        wrapped_data (str | memoryview | bytes | bytearray): The wrapped data.
        encoding (str): The encoding format (default is 'yaml').
        as_extended (bool): Wrap decoded values in Tier 2 Extended Data containers.

    Returns:
        Any: The unwrapped data.

    Raises:
        ValueError: If the encoding format is unsupported.
    """
    normalized_encoding = normalize_data_encoding(encoding)

    if normalized_encoding == "yaml":
        decoded = decode_yaml(wrapped_data)
    elif normalized_encoding == "json":
        decoded = decode_json(wrapped_data)
    elif normalized_encoding == "toml":
        decoded = decode_toml(wrapped_data)
    elif normalized_encoding == "hcl":
        decoded = decode_hcl2(wrapped_data)
    elif normalized_encoding == "raw":
        decoded = bytes_to_string(wrapped_data)
    else:
        error_message = f"Unsupported encoding format: {encoding}"
        raise ValueError(error_message)

    if as_extended:
        return extend_data(decoded)
    return decoded
