"""Test Suite for TOML Utilities.

This module contains test functions for verifying the functionality of TOML decoding
using the `extended_data` package. It specifically tests the behavior of the
`decode_toml` function when dealing with invalid TOML formats.

Functions:
    - test_decode_toml_invalid_format: Tests decoding of TOML with syntax errors.
"""

from __future__ import annotations

import datetime

from pathlib import Path

import pytest
import tomlkit

from extended_data.primitives.formats.errors import DataDecodeError
from extended_data.primitives.formats.toml import decode_toml, encode_toml


def test_decode_toml_invalid_format() -> None:
    """Reject malformed TOML through a sanitized package error."""
    invalid_toml = "token = 'super-secret"
    with pytest.raises(DataDecodeError) as exc_info:
        decode_toml(invalid_toml)

    message = str(exc_info.value)
    assert "Failed to decode TOML data" in message
    assert "line 1" in message
    assert "super-secret" not in message


def test_decode_toml_bytes_success() -> None:
    """Decode TOML from bytes."""
    result = decode_toml(b'title = "Example"\n')
    assert result == {"title": "Example"}


def test_decode_toml_invalid_bytes() -> None:
    """Raise a sanitized decode error when bytes cannot be decoded."""
    with pytest.raises(DataDecodeError, match="input bytes are not valid UTF-8"):
        decode_toml(b"\x80")


def test_encode_toml_converts_special_types() -> None:
    """Convert special types before TOML encoding."""
    result = encode_toml(
        {
            "date": datetime.date(2025, 1, 15),
            "path": Path("/tmp/example.txt"),
        }
    )

    assert 'date = "2025-01-15"' in result
    assert 'path = "/tmp/example.txt"' in result


def test_encode_toml_converts_tuple_like_composites() -> None:
    """Normalize tuples and frozensets instead of stringifying them."""
    result = encode_toml(
        {
            "items": ("alpha", "beta"),
            "values": frozenset([1, 2]),
        }
    )

    parsed = tomlkit.parse(result)
    assert parsed["items"] == ["alpha", "beta"]
    assert sorted(parsed["values"]) == [1, 2]
