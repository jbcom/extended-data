"""Test suite for extended_data.primitives.types module.

This module contains unit tests for various utility functions provided by
the type_utils module, ensuring correct functionality of type conversions,
special type handling, and error handling mechanisms.
"""

from __future__ import annotations

import datetime

from pathlib import Path
from typing import Any

import pytest

from extended_data.containers import ExtendedDict, ExtendedList, ExtendedSet, ExtendedString, ExtendedTuple
from extended_data.primitives.formats.yaml import YamlPairs, YamlTagged
from extended_data.primitives.types import (
    ConversionError,
    convert_special_type,
    convert_special_types,
    get_default_value_for_type,
    get_primitive_type_for_instance_type,
    make_hashable,
    reconstruct_special_type,
    reconstruct_special_types,
    string_to_bool,
    string_to_date,
    string_to_datetime,
    string_to_float,
    string_to_int,
    string_to_path,
    string_to_time,
    typeof,
)


# Constants for expected test values
EXPECTED_FLOAT_1 = 3.14
EXPECTED_FLOAT_2 = 42.0
EXPECTED_INT_1 = 42
EXPECTED_INT_2 = 3


@pytest.fixture(params=[("yes", True), ("no", False), ("invalid", None)])
def string_to_bool_data(request: Any) -> tuple[str, bool | None]:
    """Provides data for testing string_to_bool function.

    Yields:
        tuple[str, bool | None]: A tuple containing the input string and the expected boolean or None result.
    """
    return request.param


@pytest.fixture(params=[("3.14", EXPECTED_FLOAT_1), ("42", EXPECTED_FLOAT_2), ("invalid", None)])
def string_to_float_data(request: Any) -> tuple[str, float | None]:
    """Provides data for testing string_to_float function.

    Yields:
        tuple[str, float | None]: A tuple containing the input value and the expected float or None result.
    """
    return request.param


@pytest.fixture(params=[("42", EXPECTED_INT_1), ("3.0", EXPECTED_INT_2), ("invalid", None)])
def string_to_int_data(request: Any) -> tuple[str, int | None]:
    """Provides data for testing string_to_int function.

    Yields:
        tuple[str, int | None]: A tuple containing the input value and the expected int or None result.
    """
    return request.param


@pytest.fixture(
    params=[
        ("/valid/path", Path("/valid/path")),
        (b"/valid/bytes/path", Path("/valid/bytes/path")),
        (None, None),
        (Path("/already/path"), Path("/already/path")),
    ]
)
def valid_path_data(request: Any) -> tuple[str | bytes | Path | None, Path | None]:
    """Provides valid input and expected output pairs for testing string_to_path function.

    Yields:
        tuple[str | bytes | Path | None, Path | None]: A tuple containing the input value and the expected Path or None result.
    """
    return request.param


@pytest.fixture(params=[("invalid:://path", ValueError, True), (b"\x80invalid", ValueError, True)])
def invalid_path_data(request: Any) -> tuple[str | bytes, type[Exception], bool]:
    """Provides invalid input, expected exception type, and raise_on_error flag for testing string_to_path.

    Yields:
        tuple[str | bytes, Type[Exception], bool]: A tuple containing the input value, expected exception type, and the raise_on_error flag.
    """
    return request.param


@pytest.fixture(params=["invalid:://path", b"\x80invalid"])
def silent_invalid_path_data(request: Any) -> str | bytes:
    """Provides invalid input values for testing string_to_path when raise_on_error is False.

    Yields:
        str | bytes: The invalid input value to test.
    """
    return request.param


@pytest.fixture(
    params=[
        ("2023-09-05", datetime.date(2023, 9, 5)),
        ("2022-01-01", datetime.date(2022, 1, 1)),
        ("invalid-date", None),
    ]
)
def string_to_date_data(request: Any) -> tuple[str, datetime.date | None]:
    """Provides data for testing string_to_date function.

    Yields:
        tuple[str, datetime.date | None]: A tuple containing the input string and the expected date object or None.
    """
    return request.param


@pytest.fixture(
    params=[
        (
            "2023-09-05T12:30:00",
            datetime.datetime(2023, 9, 5, 12, 30, 0, tzinfo=datetime.UTC),
        ),
        (
            "2023-09-05 12:30:00",
            datetime.datetime(2023, 9, 5, 12, 30, 0, tzinfo=datetime.UTC),
        ),
        (
            "2023-09-05T12:30:00.123456",
            datetime.datetime(2023, 9, 5, 12, 30, 0, 123456, tzinfo=datetime.UTC),
        ),
        ("invalid-datetime", None),
    ]
)
def string_to_datetime_data(request: Any) -> tuple[str, datetime.datetime | None]:
    """Provides data for testing string_to_datetime function.

    Yields:
        tuple[str, datetime.datetime | None]: A tuple containing the input string and the expected datetime object or None.
    """
    return request.param


@pytest.fixture(
    params=[
        ("12:30:00", datetime.time(12, 30, 0)),
        ("12:30", datetime.time(12, 30, 0)),
        ("12:30:00.123456", datetime.time(12, 30, 0, 123456)),
        ("invalid-time", None),
    ]
)
def string_to_time_data(request: Any) -> tuple[str, datetime.time | None]:
    """Provides data for testing string_to_time function.

    Yields:
        tuple[str, datetime.time | None]: A tuple containing the input string and the expected time object or None.
    """
    return request.param


def test_string_to_bool(string_to_bool_data: tuple[str, bool | None]) -> None:
    """Tests converting a string to a boolean value.

    Args:
        string_to_bool_data (tuple[str, bool | None]): A fixture providing the input string and the expected boolean or None result.

    Asserts:
        The result of string_to_bool is True for truthy strings, False for falsy strings, and raises a ConversionError for invalid strings if specified.
    """
    val, expected = string_to_bool_data
    assert string_to_bool(val) == expected
    if expected is None and val == "invalid":
        with pytest.raises(ConversionError, match=r"Invalid <class 'bool'> value: 'invalid'"):
            string_to_bool(val, raise_on_error=True)


def test_string_to_bool_passthrough_for_bool_and_none() -> None:
    """Return boolean and None inputs unchanged."""
    assert string_to_bool(True) is True
    assert string_to_bool(False) is False
    assert string_to_bool(None) is None


def test_string_to_bool_rejects_non_strings_when_requested() -> None:
    """Reject unsupported non-string inputs when raise_on_error is enabled."""
    with pytest.raises(ConversionError, match=r"Invalid <class 'bool'> value: 123"):
        string_to_bool(123, raise_on_error=True)


def test_string_type_converters_accept_extended_string_values() -> None:
    """Type conversion primitives compose with Tier 2 ExtendedString values."""
    assert string_to_bool(ExtendedString("true")) is True
    assert string_to_float(ExtendedString("3.14")) == EXPECTED_FLOAT_1
    assert string_to_int(ExtendedString("42")) == EXPECTED_INT_1
    assert string_to_date(ExtendedString("2023-09-05")) == datetime.date(2023, 9, 5)
    assert string_to_datetime(ExtendedString("2023-09-05T12:30:00")) == datetime.datetime(
        2023,
        9,
        5,
        12,
        30,
        0,
        tzinfo=datetime.UTC,
    )
    assert string_to_time(ExtendedString("12:30")) == datetime.time(12, 30, 0)
    assert string_to_path(ExtendedString("/valid/path")) == Path("/valid/path")


def test_string_to_float(string_to_float_data: tuple[str, float | None]) -> None:
    """Tests converting a string to a float value.

    Args:
        string_to_float_data (tuple[str, float | None]): A fixture providing the input value and the expected float or None result.

    Asserts:
        The result of string_to_float matches the expected float value and raises a ConversionError for invalid strings if specified.
    """
    val, expected = string_to_float_data
    assert string_to_float(val) == expected
    if expected is None and val == "invalid":
        with pytest.raises(ConversionError, match=r"Invalid <class 'float'> value: 'invalid'"):
            string_to_float(val, raise_on_error=True)


def test_string_to_float_wraps_float_value_errors(mocker) -> None:
    """Surface float conversion failures as ConversionError when requested."""
    mocker.patch("builtins.float", side_effect=ValueError("boom"))

    with pytest.raises(ConversionError, match=r"Invalid .* value: '3.14'"):
        string_to_float("3.14", raise_on_error=True)


def test_string_to_float_swallows_float_value_errors_when_not_requested(mocker) -> None:
    """Return None when float conversion fails and raise_on_error is disabled."""
    mocker.patch("builtins.float", side_effect=ValueError("boom"))
    assert string_to_float("3.14") is None


def test_string_to_int(string_to_int_data: tuple[str, int | None]) -> None:
    """Tests converting a string to an integer value.

    Args:
        string_to_int_data (tuple[str, int | None]): A fixture providing the input value and the expected int or None result.

    Asserts:
        The result of string_to_int matches the expected integer value and raises a ConversionError for invalid strings if specified.
    """
    val, expected = string_to_int_data
    assert string_to_int(val) == expected
    if expected is None and val == "invalid":
        with pytest.raises(ConversionError, match=r"Invalid <class 'int'> value: 'invalid'"):
            string_to_int(val, raise_on_error=True)


def test_string_to_int_wraps_nested_conversion_errors(mocker) -> None:
    """Map nested float conversion failures to integer conversion failures."""
    mocker.patch(
        "extended_data.primitives.types.string_to_float",
        side_effect=ConversionError(float, "3.14"),
    )

    with pytest.raises(ConversionError, match=r"Invalid <class 'int'> value: '3.14'"):
        string_to_int("3.14", raise_on_error=True)


def test_string_to_int_swallows_nested_conversion_errors_when_not_requested(mocker) -> None:
    """Return None when nested conversion fails and raise_on_error is disabled."""
    mocker.patch(
        "extended_data.primitives.types.string_to_float",
        side_effect=ConversionError(float, "3.14"),
    )

    assert string_to_int("3.14") is None


def test_string_to_int_raises_when_nested_conversion_returns_none(mocker) -> None:
    """Raise an integer conversion error when nested conversion returns no value."""
    mocker.patch("extended_data.primitives.types.string_to_float", return_value=None)

    with pytest.raises(ConversionError, match=r"Invalid <class 'int'> value: '3.14'"):
        string_to_int("3.14", raise_on_error=True)


def test_string_to_path(
    valid_path_data: tuple[str | bytes | Path | None, Path | None],
) -> None:
    """Tests the string_to_path function for converting valid inputs into Path objects.

    Args:
        valid_path_data (tuple[str | bytes | Path | None, Path | None]): A fixture providing the input value and the expected Path or None result.

    Asserts:
        The result of string_to_path matches the expected Path object or None.
    """
    value, expected = valid_path_data
    assert string_to_path(value) == expected


def test_string_to_path_invalid(
    invalid_path_data: tuple[str | bytes, type[Exception], bool],
) -> None:
    """Tests the string_to_path function for handling invalid inputs that should raise exceptions.

    Args:
        invalid_path_data (tuple[str | bytes, Type[Exception], bool]): A fixture providing the input value, expected exception type, and the raise_on_error flag.

    Asserts:
        The string_to_path function raises the expected exception with the correct error message when the raise_on_error flag is set to True.
    """
    value, expected_exception, raise_on_error = invalid_path_data
    with pytest.raises(expected_exception, match=r"Invalid <class 'pathlib.Path'> value"):
        string_to_path(value, raise_on_error=raise_on_error)


def test_string_to_path_invalid_silent(silent_invalid_path_data: str | bytes) -> None:
    """Tests the string_to_path function with invalid inputs when fail_silently is set to True.

    Args:
        silent_invalid_path_data (str | bytes): A fixture providing the invalid input value to test.

    Asserts:
        The string_to_path function returns None when the input is invalid and the raise_on_error flag is False.
    """
    assert string_to_path(silent_invalid_path_data) is None


def test_string_to_date(string_to_date_data: tuple[str, datetime.date | None]) -> None:
    """Tests converting a string to a date value.

    Args:
        string_to_date_data (tuple[str, datetime.date | None]): A fixture providing the input string and the expected date object or None.

    Asserts:
        The result of string_to_date matches the expected date value and raises a ConversionError for invalid strings if specified.
    """
    val, expected = string_to_date_data
    assert string_to_date(val) == expected
    if expected is None and val == "invalid-date":
        with pytest.raises(
            ConversionError,
            match=r"Invalid <class 'datetime.date'> value: 'invalid-date'",
        ):
            string_to_date(val, raise_on_error=True)


def test_string_to_date_invalid_matching_pattern_raises() -> None:
    """Reject impossible calendar dates that still match the date pattern."""
    assert string_to_date("2023-13-40") is None
    with pytest.raises(ConversionError, match=r"Invalid <class 'datetime.date'> value: '2023-13-40'"):
        string_to_date("2023-13-40", raise_on_error=True)


def test_string_to_datetime(
    string_to_datetime_data: tuple[str, datetime.datetime | None],
) -> None:
    """Tests converting a string to a datetime value.

    Args:
        string_to_datetime_data (tuple[str, datetime.datetime | None]): A fixture providing the input string and the expected datetime object or None.

    Asserts:
        The result of string_to_datetime matches the expected datetime value and raises a ConversionError for invalid strings if specified.
    """
    val, expected = string_to_datetime_data
    assert string_to_datetime(val) == expected
    if expected is None and val == "invalid-datetime":
        with pytest.raises(
            ConversionError,
            match=r"Invalid <class 'datetime.datetime'> value: 'invalid-datetime'",
        ):
            string_to_datetime(val, raise_on_error=True)


def test_string_to_datetime_invalid_matching_pattern_raises() -> None:
    """Reject impossible datetimes that still match the datetime pattern."""
    invalid_value = "2023-13-05T25:61:00"
    assert string_to_datetime(invalid_value) is None
    with pytest.raises(ConversionError, match=r"Invalid <class 'datetime.datetime'> value: '2023-13-05T25:61:00'"):
        string_to_datetime(invalid_value, raise_on_error=True)


def test_string_to_datetime_preserves_explicit_timezone() -> None:
    """Keep explicit timezone offsets instead of forcing UTC."""
    result = string_to_datetime("2023-09-05T12:30:00+02:00")

    assert result == datetime.datetime(2023, 9, 5, 12, 30, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=2)))


def test_string_to_time(string_to_time_data: tuple[str, datetime.time | None]) -> None:
    """Tests converting a string to a time value.

    Args:
        string_to_time_data (tuple[str, datetime.time | None]): A fixture providing the input string and the expected time object or None.

    Asserts:
        The result of string_to_time matches the expected time value and raises a ConversionError for invalid strings if specified.
    """
    val, expected = string_to_time_data
    assert string_to_time(val) == expected
    if expected is None and val == "invalid-time":
        with pytest.raises(
            ConversionError,
            match=r"Invalid <class 'datetime.time'> value: 'invalid-time'",
        ):
            string_to_time(val, raise_on_error=True)


def test_string_to_time_invalid_matching_pattern_raises() -> None:
    """Reject impossible times that still match the time pattern."""
    invalid_value = "25:61:00"
    assert string_to_time(invalid_value) is None
    with pytest.raises(ConversionError, match=r"Invalid <class 'datetime.time'> value: '25:61:00'"):
        string_to_time(invalid_value, raise_on_error=True)


# Test for get_default_value_for_type function
@pytest.mark.parametrize(
    ("input_type", "expected"),
    [
        (list, []),
        (dict, {}),
        (str, ""),
        (int, None),
        (type(None), None),
    ],
)
def test_get_default_value_for_type(input_type: type, expected: Any) -> None:
    """Tests the default value returned for various types."""
    assert get_default_value_for_type(input_type) == expected


# Test for get_primitive_type_for_instance_type function
@pytest.mark.parametrize(
    ("value", "expected_type"),
    [
        (42, int),
        (3.14, float),
        (True, bool),
        ("hello", str),
        (b"bytes", bytes),
        ([1, 2, 3], list),
        ((1, 2, 3), list),
        ({"key": "value"}, dict),
        ({1, 2}, set),
        (ExtendedString("hello"), str),
        (ExtendedList([1, 2, 3]), list),
        (ExtendedTuple((1, 2, 3)), list),
        (ExtendedDict({"key": "value"}), dict),
        (ExtendedSet({1, 2}), set),
        (None, type(None)),
        (object(), object),
    ],
)
def test_get_primitive_type_for_instance_type(value: Any, expected_type: type) -> None:
    """Tests the primitive type returned for various instance types."""
    assert get_primitive_type_for_instance_type(value) == expected_type


# Test for typeof function
@pytest.mark.parametrize(
    ("item", "primitive_only", "expected_type"),
    [
        (42, False, int),
        (42, True, int),
        ([1, 2, 3], False, list),
        ([1, 2, 3], True, list),
        ({"key": "value"}, False, dict),
        ({"key": "value"}, True, dict),
        (ExtendedString("hello"), False, ExtendedString),
        (ExtendedString("hello"), True, str),
        (ExtendedList([1, 2, 3]), False, ExtendedList),
        (ExtendedList([1, 2, 3]), True, list),
        (ExtendedDict({"key": "value"}), False, ExtendedDict),
        (ExtendedDict({"key": "value"}), True, dict),
    ],
)
def test_typeof(item: Any, primitive_only: bool, expected_type: type) -> None:
    """Tests typeof function with and without primitive_only flag."""
    assert typeof(item, primitive_only) == expected_type


# Test for convert_special_type function
@pytest.mark.parametrize(
    ("obj", "expected"),
    [
        (datetime.date(2023, 9, 5), "2023-09-05"),
        (
            datetime.datetime(2023, 9, 5, 12, 30, tzinfo=datetime.UTC),
            "2023-09-05T12:30:00",
        ),
        (Path("/some/path"), "/some/path"),
        ("simple string", "simple string"),
        (123, 123),
        (3.14, 3.14),
    ],
)
def test_convert_special_type(obj: Any, expected: Any) -> None:
    """Tests conversion of special types to simpler forms."""
    assert convert_special_type(obj) == expected


def test_convert_special_type_handles_yaml_wrappers_and_custom_objects() -> None:
    """Convert YAML wrapper types and unknown objects to simple forms."""

    class CustomObject:
        def __str__(self) -> str:
            return "custom-object"

    assert convert_special_type(YamlTagged("!Ref", "BucketName")) == "BucketName"
    assert convert_special_type(YamlTagged("!Ref", {"path": Path("/tmp/config.yml")})) == {"path": "/tmp/config.yml"}
    assert convert_special_type(YamlPairs([("key", "value")])) == [["key", "value"]]
    assert convert_special_type(CustomObject()) == "custom-object"


def test_convert_special_type_handles_mappings_and_sequences_directly() -> None:
    """Normalize container inputs passed directly to convert_special_type."""
    assert convert_special_type({"path": Path("/tmp/config.yml")}) == {"path": "/tmp/config.yml"}
    assert convert_special_type((Path("/tmp/a"), datetime.date(2025, 1, 15))) == ["/tmp/a", "2025-01-15"]


def test_convert_special_types_handles_extended_containers() -> None:
    """Normalize Tier 2 containers without stringifying nested collections."""
    value = ExtendedDict(
        {
            "enabled": ExtendedString("true"),
            "paths": ExtendedList([Path("/tmp/a"), datetime.date(2025, 1, 15)]),
            "tags": ExtendedSet({ExtendedString("api")}),
        }
    )

    result = convert_special_types(value)

    assert result["enabled"] == "true"
    assert result["paths"] == ["/tmp/a", "2025-01-15"]
    assert result["tags"] == ["api"]


# Test for convert_special_types function
@pytest.mark.parametrize(
    ("obj", "expected"),
    [
        ({"date": datetime.date(2023, 9, 5)}, {"date": "2023-09-05"}),
        (
            [
                "/path/to/file",
                datetime.datetime(2023, 9, 5, 12, 30, tzinfo=datetime.UTC),
            ],
            ["/path/to/file", "2023-09-05T12:30:00"],
        ),
        ({datetime.date(2023, 9, 5)}, ["2023-09-05"]),  # Update expected format to list
        (
            ["text", 123, {"key": Path("/some/path")}],
            ["text", 123, {"key": "/some/path"}],
        ),
    ],
)
def test_convert_special_types(obj: Any, expected: Any) -> None:
    """Tests conversion of nested special types to simpler forms."""
    assert convert_special_types(obj) == expected


def test_convert_special_types_handles_tuple_frozenset_and_yaml_pairs() -> None:
    """Normalize composite container types consistently across serializers."""
    result = convert_special_types(
        {
            "tuple": (Path("/tmp/a"), datetime.date(2025, 1, 15)),
            "frozenset": frozenset([1, 2]),
            "pairs": YamlPairs([("path", Path("/tmp/b"))]),
        }
    )

    assert result["tuple"] == ["/tmp/a", "2025-01-15"]
    assert sorted(result["frozenset"]) == [1, 2]
    assert result["pairs"] == [["path", "/tmp/b"]]


@pytest.mark.parametrize(
    ("obj", "expected"),
    [
        ("2023-09-05", datetime.date(2023, 9, 5)),  # Date string to datetime.date
        (
            "2023-09-05T12:30:00",
            datetime.datetime(2023, 9, 5, 12, 30, tzinfo=datetime.UTC),
        ),  # Datetime string to datetime.datetime
        ("12:30:00", datetime.time(12, 30, 0)),  # Time string to datetime.time
        ("/some/path", Path("/some/path")),  # Path string to Path
        ("simple string", "simple string"),  # Simple string remains unchanged
        ("123", 123),  # Numeric string to integer
        ("-123", -123),  # Negative numeric string to integer
        ("3.14", 3.14),  # Numeric string to float
        ("-3.14", -3.14),  # Negative numeric string to float
        ("true", True),  # Boolean string to bool
        ("false", False),
        ("None", None),  # "None" string to NoneType
        ("null", None),  # JSON null string to NoneType
        ("", ""),  # Empty string remains unchanged
    ],
)
def test_reconstruct_special_type(obj: str, expected: Any) -> None:
    """Tests reconstruction of strings back into their original special types."""
    assert reconstruct_special_type(obj, fail_silently=False) == expected


@pytest.mark.parametrize(
    ("obj", "expected"),
    [
        ("a: 1\n", {"a": 1}),
        ('{"a":1}', {"a": 1}),
    ],
)
def test_reconstruct_special_type_decodes_yaml_and_json(obj: str, expected: Any) -> None:
    """Reconstruct YAML and JSON string documents into structured data."""
    assert reconstruct_special_type(obj, fail_silently=False) == expected


@pytest.mark.parametrize("obj", ["a: [1\n", '{"a":1,}'])
def test_reconstruct_special_type_raises_on_invalid_structured_data(obj: str) -> None:
    """Raise ConversionError when malformed YAML or JSON decoding fails."""
    with pytest.raises(ConversionError):
        reconstruct_special_type(obj, fail_silently=False)


@pytest.mark.parametrize("obj", ["a: [1\n", '{"a":1,}'])
def test_reconstruct_special_type_fails_silently_for_invalid_structured_data(obj: str) -> None:
    """Return the original text when malformed structured data is allowed to fail silently."""
    assert reconstruct_special_type(obj, fail_silently=True) == obj


# Test for reconstruct_special_types function
@pytest.mark.parametrize(
    ("obj", "expected"),
    [
        ({"date": "2023-09-05"}, {"date": datetime.date(2023, 9, 5)}),
        (
            ["/path/to/file", "2023-09-05T12:30:00"],
            [
                Path("/path/to/file"),
                datetime.datetime(2023, 9, 5, 12, 30, tzinfo=datetime.UTC),
            ],
        ),
        (
            ["text", "123", {"key": "/some/path"}],
            ["text", 123, {"key": Path("/some/path")}],
        ),
        (
            ["2023-09-05", {"nested": ["2023-09-05T12:30:00"]}],
            [
                datetime.date(2023, 9, 5),
                {"nested": [datetime.datetime(2023, 9, 5, 12, 30, tzinfo=datetime.UTC)]},
            ],
        ),
        (
            ["true", "false", "None"],
            [True, False, None],
        ),  # Test boolean and None reconstruction in a list
    ],
)
def test_reconstruct_special_types(obj: Any, expected: Any) -> None:
    """Tests reconstruction of nested structures back into their original types."""
    assert reconstruct_special_types(obj, fail_silently=False) == expected


def test_reconstruct_special_types_handles_sets() -> None:
    """Reconstruct values contained in sets."""
    result = reconstruct_special_types({"2023-09-05", "true"}, fail_silently=False)
    assert result == {datetime.date(2023, 9, 5), True}


def test_reconstruct_special_types_handles_tuples_and_frozensets() -> None:
    """Reconstruct values inside immutable composite containers."""
    tuple_result = reconstruct_special_types(("2023-09-05", "true"), fail_silently=False)
    frozenset_result = reconstruct_special_types(frozenset(["2023-09-05", "true"]), fail_silently=False)

    assert tuple_result == (datetime.date(2023, 9, 5), True)
    assert frozenset_result == frozenset([datetime.date(2023, 9, 5), True])


def test_reconstruct_special_types_handles_extended_containers() -> None:
    """Reconstruct special values inside Tier 2 containers."""
    value = ExtendedDict(
        {
            "enabled": ExtendedString("true"),
            "count": ExtendedString("5"),
            "items": ExtendedList([ExtendedString("2023-09-05")]),
            "tags": ExtendedSet({ExtendedString("false")}),
        }
    )

    result = reconstruct_special_types(value, fail_silently=False)

    assert result["enabled"] is True
    assert result["count"] == 5
    assert result["items"] == [datetime.date(2023, 9, 5)]
    assert result["tags"] == {False}


def test_reconstruct_special_types_leaves_non_container_values_alone() -> None:
    """Pass through values that do not need recursive reconstruction."""
    assert reconstruct_special_types(123, fail_silently=False) == 123


# Test for reconstruct_special_type with fail_silently=True
def test_reconstruct_special_type_fail_silently() -> None:
    """Tests reconstruction with fail_silently=True, ensuring no exception is raised and original value is returned."""
    assert reconstruct_special_type("invalid path:://example") == "invalid path:://example"
    assert reconstruct_special_type("not a number", fail_silently=True) == "not a number"


@pytest.mark.parametrize(
    ("obj", "expected"),
    [
        (
            [{"nested": ["true", {"deep": "2023-09-05T12:30:00"}]}],
            [
                {
                    "nested": [
                        True,
                        {"deep": datetime.datetime(2023, 9, 5, 12, 30, tzinfo=datetime.UTC)},
                    ]
                }
            ],
        ),
    ],
)
def test_reconstruct_deeply_nested_structure(obj: Any, expected: Any) -> None:
    """Tests reconstruction of deeply nested structures."""
    assert reconstruct_special_types(obj, fail_silently=False) == expected


class TestMakeHashable:
    """Tests for the make_hashable function."""

    def test_primitives_unchanged(self) -> None:
        """Test that primitive types are returned unchanged."""
        assert make_hashable("string") == "string"
        assert make_hashable(42) == 42
        assert make_hashable(3.14) == 3.14
        assert make_hashable(True) is True
        assert make_hashable(None) is None

    def test_list_to_tuple(self) -> None:
        """Test that lists are converted to tuples."""
        assert make_hashable([1, 2, 3]) == (1, 2, 3)
        assert make_hashable(["a", "b"]) == ("a", "b")

    def test_tuple_stays_tuple(self) -> None:
        """Test that tuples remain tuples."""
        assert make_hashable((1, 2, 3)) == (1, 2, 3)

    def test_dict_to_frozenset(self) -> None:
        """Test that dicts are converted to frozensets of tuples."""
        result = make_hashable({"a": 1, "b": 2})
        assert isinstance(result, frozenset)
        assert result == frozenset([("a", 1), ("b", 2)])

    def test_nested_structure(self) -> None:
        """Test that nested structures are recursively converted."""
        result = make_hashable({"key": [1, 2, {"nested": "value"}]})
        assert isinstance(result, frozenset)
        # The list should be converted to tuple, and nested dict to frozenset
        expected_nested = frozenset([("nested", "value")])
        expected_list = (1, 2, expected_nested)
        assert result == frozenset([("key", expected_list)])

    def test_dict_with_mixed_keys_sorts_stably(self) -> None:
        """Mixed key types should still normalize without raising TypeError."""
        result = make_hashable({Path("/tmp/a"): "path", "name": "value"})
        assert isinstance(result, frozenset)
        assert (Path("/tmp/a"), "path") not in result

    def test_cyclic_list_uses_cycle_marker(self) -> None:
        """Self-referential lists should normalize without RecursionError."""
        cyclic: list[object] = []
        cyclic.append(cyclic)

        assert make_hashable(cyclic) == (("__cycle__", "list"),)

    def test_result_is_hashable(self) -> None:
        """Test that the result can be used as a dict key."""
        complex_obj = {"a": [1, 2], "b": {"c": 3}}
        hashable = make_hashable(complex_obj)
        # Should not raise - can be used as dict key
        test_dict = {hashable: "value"}
        assert test_dict[hashable] == "value"

    def test_custom_object_to_string(self) -> None:
        """Test that custom objects are converted to string."""

        class CustomClass:
            def __str__(self) -> str:
                return "custom_str"

        result = make_hashable(CustomClass())
        assert result == "custom_str"
