"""This module provides utilities for encoding and decoding data to and from Base64 format.

It includes functions to encode data to Base64 strings, with optional data
wrapping for export, and to decode Base64 strings back to their original data.
"""

from __future__ import annotations

from base64 import b64decode, b64encode
from typing import Any

from extended_data.export_utils import wrap_raw_data_for_export
from extended_data.import_utils import unwrap_raw_data_from_import


def base64_encode(raw_data: str | bytes, wrap_raw_data: bool = True) -> str:
    """Encodes data to base64 format.

    Args:
        raw_data (str | bytes): The data to encode.
        wrap_raw_data (bool): Whether to wrap the raw data for export.

    Returns:
        str: The base64 encoded string.
    """
    if wrap_raw_data:
        if isinstance(raw_data, bytes):
            raw_data = raw_data.decode("utf-8")
        raw_data = wrap_raw_data_for_export(raw_data).encode("utf-8")
    elif isinstance(raw_data, str):
        raw_data = raw_data.encode("utf-8")

    return b64encode(raw_data).decode("utf-8")


def base64_decode(
    encoded_data: str,
    unwrap_raw_data: bool = True,
    encoding: str = "yaml",
) -> Any:
    """Decodes data from base64 format.

    Args:
        encoded_data (str): The base64 encoded string to decode.
        unwrap_raw_data (bool): Whether to unwrap the raw data after decoding.
        encoding (str): The encoding format used for wrapping (default is 'yaml').

    Returns:
        Any: The decoded bytes when ``unwrap_raw_data`` is ``False``, otherwise
        the decoded Python object or raw text after UTF-8 decoding.
    """
    decoded_bytes = b64decode(encoded_data)
    if not unwrap_raw_data:
        return decoded_bytes

    try:
        decoded_text = decoded_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        message = "Decoded Base64 payload is not valid UTF-8 text."
        raise ValueError(message) from exc

    return unwrap_raw_data_from_import(decoded_text, encoding=encoding)
