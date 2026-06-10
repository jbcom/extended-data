"""This module contains test functions for encoding and decoding Base64 data using the utility functions from the
`extended_data` package. The tests cover various scenarios, including encoding and decoding strings and bytes,
with and without additional wrapping of the raw data.

Functions:
    - test_base64_encode_string: Tests Base64 encoding of a standard string.
    - test_base64_encode_bytes: Tests Base64 encoding of bytes data.
    - test_base64_encode_with_wrap: Tests Base64 encoding of a string with wrapping.
    - test_base64_encode_with_bytes_and_wrap: Tests Base64 encoding of bytes data with wrapping.
    - test_base64_encode_empty_string: Tests Base64 encoding of an empty string.
    - test_base64_encode_empty_bytes: Tests Base64 encoding of empty bytes data.
    - test_base64_encode_empty_string_with_wrap: Tests Base64 encoding of an empty string with wrapping.
    - test_base64_encode_empty_bytes_with_wrap: Tests Base64 encoding of empty bytes data with wrapping.
    - test_base64_decode_string: Tests Base64 decoding of a standard encoded string.
    - test_base64_decode_bytes: Tests Base64 decoding of bytes data.
    - test_base64_decode_with_unwrap: Tests Base64 decoding with unwrapping.
"""

from __future__ import annotations

import base64

import pytest

from extended_data.io.base64 import base64_decode, base64_encode
from extended_data.io.exporters import wrap_raw_data_for_export


def test_base64_encode_string() -> None:
    """Tests Base64 encoding of a standard string.

    Asserts:
        The result of base64_encode matches the expected Base64 encoded string.
    """
    raw_data = "test data"
    expected_encoded_data = base64.b64encode(raw_data.encode("utf-8")).decode("utf-8")
    result = base64_encode(raw_data, wrap_raw_data=False)
    assert result == expected_encoded_data, f"Expected {expected_encoded_data}, but got {result}."


def test_base64_encode_bytes() -> None:
    """Tests Base64 encoding of bytes data.

    Asserts:
        The result of base64_encode matches the expected Base64 encoded string.
    """
    raw_data = b"test data"
    expected_encoded_data = base64.b64encode(raw_data).decode("utf-8")
    result = base64_encode(raw_data, wrap_raw_data=False)
    assert result == expected_encoded_data, f"Expected {expected_encoded_data}, but got {result}."


def test_base64_encode_with_wrap() -> None:
    """Tests Base64 encoding of a string with wrapping.

    Asserts:
        The result of base64_encode matches the expected Base64 encoded string with wrapping applied.
    """
    raw_data = "test data"
    wrapped_data = wrap_raw_data_for_export(raw_data).encode("utf-8")
    expected_encoded_data = base64.b64encode(wrapped_data).decode("utf-8")
    result = base64_encode(raw_data, wrap_raw_data=True)
    assert result == expected_encoded_data, f"Expected {expected_encoded_data}, but got {result}."


def test_base64_encode_with_bytes_and_wrap() -> None:
    """Tests Base64 encoding of bytes data with wrapping.

    Asserts:
        The result of base64_encode matches the expected Base64 encoded string with wrapping applied.
    """
    raw_data = b"test data"
    wrapped_data = wrap_raw_data_for_export(raw_data.decode("utf-8")).encode("utf-8")
    expected_encoded_data = base64.b64encode(wrapped_data).decode("utf-8")
    result = base64_encode(raw_data, wrap_raw_data=True)
    assert result == expected_encoded_data, f"Expected {expected_encoded_data}, but got {result}."


def test_base64_encode_empty_string() -> None:
    """Tests Base64 encoding of an empty string.

    Asserts:
        The result of base64_encode matches the expected Base64 encoded string for an empty input.
    """
    raw_data = ""
    expected_encoded_data = base64.b64encode(raw_data.encode("utf-8")).decode("utf-8")
    result = base64_encode(raw_data, wrap_raw_data=False)
    assert result == expected_encoded_data, f"Expected {expected_encoded_data}, but got {result}."


def test_base64_encode_empty_bytes() -> None:
    """Tests Base64 encoding of empty bytes data.

    Asserts:
        The result of base64_encode matches the expected Base64 encoded string for empty bytes input.
    """
    raw_data = b""
    expected_encoded_data = base64.b64encode(raw_data).decode("utf-8")
    result = base64_encode(raw_data, wrap_raw_data=False)
    assert result == expected_encoded_data, f"Expected {expected_encoded_data}, but got {result}."


def test_base64_encode_empty_string_with_wrap() -> None:
    """Tests Base64 encoding of an empty string with wrapping.

    Asserts:
        The result of base64_encode matches the expected Base64 encoded string for an empty input with wrapping.
    """
    raw_data = ""
    wrapped_data = wrap_raw_data_for_export(raw_data).encode("utf-8")
    expected_encoded_data = base64.b64encode(wrapped_data).decode("utf-8")
    result = base64_encode(raw_data, wrap_raw_data=True)
    assert result == expected_encoded_data, f"Expected {expected_encoded_data}, but got {result}."


def test_base64_encode_empty_bytes_with_wrap() -> None:
    """Tests Base64 encoding of empty bytes data with wrapping.

    Asserts:
        The result of base64_encode matches the expected Base64 encoded string for empty bytes input with wrapping.
    """
    raw_data = b""
    wrapped_data = wrap_raw_data_for_export(raw_data.decode("utf-8")).encode("utf-8")
    expected_encoded_data = base64.b64encode(wrapped_data).decode("utf-8")
    result = base64_encode(raw_data, wrap_raw_data=True)
    assert result == expected_encoded_data, f"Expected {expected_encoded_data}, but got {result}."


def test_base64_decode_string() -> None:
    """Tests Base64 decoding of a standard encoded string.

    Asserts:
        The result of base64_decode matches the expected decoded bytes.
    """
    encoded_data = "dGVzdCBkYXRh"
    expected_decoded_data = b"test data"
    result = base64_decode(encoded_data, unwrap_raw_data=False)
    assert result == expected_decoded_data, f"Expected {expected_decoded_data}, but got {result}."


def test_base64_decode_bytes() -> None:
    """Tests Base64 decoding of bytes data.

    Asserts:
        The result of base64_decode matches the expected decoded bytes.
    """
    encoded_data = "dGVzdCBkYXRh"
    expected_decoded_data = b"test data"
    result = base64_decode(encoded_data, unwrap_raw_data=False)
    assert result == expected_decoded_data, f"Expected {expected_decoded_data}, but got {result}."


def test_base64_decode_with_unwrap() -> None:
    """Tests Base64 decoding with unwrapping.

    Asserts:
        The result of base64_decode matches the expected decoded string with unwrapping applied.
    """
    raw_data = "test data"
    wrapped_data = wrap_raw_data_for_export(raw_data)
    encoded_data = base64.b64encode(wrapped_data.encode("utf-8")).decode("utf-8")
    result = base64_decode(encoded_data, unwrap_raw_data=True)
    assert result == raw_data, f"Expected {raw_data}, but got {result}."


def test_base64_decode_with_raw_unwrap() -> None:
    """Raw unwrap should return the decoded string without parser coercion."""
    encoded_data = base64.b64encode(b"plain text").decode("utf-8")
    result = base64_decode(encoded_data, unwrap_raw_data=True, encoding="raw")
    assert result == "plain text"


def test_base64_decode_with_tf_alias_unwrap() -> None:
    """Terraform aliases should unwrap through the HCL decoder."""
    hcl_data = 'locals { region = "us-east-1" }'
    encoded_data = base64.b64encode(hcl_data.encode("utf-8")).decode("utf-8")
    result = base64_decode(encoded_data, unwrap_raw_data=True, encoding="tf")
    assert result == {"locals": [{"region": "us-east-1"}]}


def test_base64_decode_rejects_non_utf8_when_unwrapping() -> None:
    """Raise a clear error when wrapped decoding requires non-text bytes to be parsed."""
    encoded_data = base64.b64encode(b"\xff\xfe").decode("utf-8")

    with pytest.raises(ValueError, match="not valid UTF-8 text"):
        base64_decode(encoded_data, unwrap_raw_data=True)
