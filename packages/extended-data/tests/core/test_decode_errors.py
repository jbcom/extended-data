"""Direct tests for the shared decode-error helpers."""

from __future__ import annotations

from extended_data.primitives.formats.errors import DataDecodeError, invalid_utf8_error


def test_from_exception_builds_sanitized_error() -> None:
    """DataDecodeError.from_exception should translate parser attributes without source snippets."""

    class FakeParserError(Exception):
        msg = "unexpected token"
        lineno = 3
        colno = 12

    err = DataDecodeError.from_exception("YAML", FakeParserError("whatever source text"))

    assert err.format_name == "YAML"
    assert err.reason == "unexpected token"
    assert err.line == 3
    assert err.column == 12
    message = str(err)
    assert "Failed to decode YAML data" in message
    assert "unexpected token" in message
    assert "line 3" in message
    assert "column 12" in message
    assert "whatever source text" not in message


def test_from_exception_falls_back_to_type_name_when_no_msg() -> None:
    """When a parser exposes no msg/problem attr, the reason should be the exception type name."""

    class BareError(Exception):
        pass

    err = DataDecodeError.from_exception("JSON", BareError())

    assert err.reason == "BareError"
    assert err.line is None
    assert err.column is None


def test_from_exception_extracts_yaml_problem_mark() -> None:
    """The YAML parser exposes problem_mark; from_exception should honor it."""

    class Mark:
        line = 5
        column = 9

    class YamlishError(Exception):
        problem_mark = Mark()

    err = DataDecodeError.from_exception("YAML", YamlishError())

    assert err.line == 6
    assert err.column == 10


def test_invalid_utf8_error_returns_data_decode_error() -> None:
    """invalid_utf8_error should return a DataDecodeError with the canonical reason text."""
    err = invalid_utf8_error("TOML")

    assert isinstance(err, DataDecodeError)
    assert err.format_name == "TOML"
    assert err.reason == "input bytes are not valid UTF-8"
    assert "input bytes are not valid UTF-8" in str(err)


def test_data_decode_error_message_without_reason_or_position() -> None:
    """A bare DataDecodeError should still render a valid message."""
    err = DataDecodeError("HCL")

    assert str(err) == "Failed to decode HCL data."
    assert err.reason is None
    assert err.line is None
    assert err.column is None
