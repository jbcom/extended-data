"""Tests for import utility helpers."""

from __future__ import annotations

import pytest

from extended_data.containers import ExtendedDict, ExtendedList, ExtendedString
from extended_data.io.importers import unwrap_raw_data_from_import


@pytest.mark.parametrize(
    ("wrapped_data", "encoding", "expected"),
    [
        ("key: value\n", "yaml", {"key": "value"}),
        (b"key: value\n", "yaml", {"key": "value"}),
        ("key: value\n", "yml", {"key": "value"}),
        ('{"key":"value"}', "JSON", {"key": "value"}),
        ('title = "Example"\n', "toml", {"title": "Example"}),
        ('title = "Example"\n', "tml", {"title": "Example"}),
        ('locals { region = "us-east-1" }', "hcl", {"locals": [{"region": "us-east-1"}]}),
        ('locals { region = "us-east-1" }', "tf", {"locals": [{"region": "us-east-1"}]}),
        ('locals { region = "us-east-1" }', "tfvars", {"locals": [{"region": "us-east-1"}]}),
        ("plain text", "raw", "plain text"),
    ],
)
def test_unwrap_raw_data_from_import(
    wrapped_data: str | bytes,
    encoding: str,
    expected: object,
) -> None:
    """Decode supported import encodings."""
    assert unwrap_raw_data_from_import(wrapped_data, encoding) == expected


def test_unwrap_raw_data_from_import_rejects_unsupported_encoding() -> None:
    """Reject unsupported import encodings."""
    with pytest.raises(ValueError, match="Unsupported encoding format: xml"):
        unwrap_raw_data_from_import("<key>value</key>", "xml")


def test_unwrap_raw_data_from_import_can_return_extended_containers() -> None:
    """Decoded imports can opt into the Tier 2 container layer."""
    result = unwrap_raw_data_from_import(
        '{"service": {"name": "api"}, "ports": [8080]}',
        encoding="json",
        as_extended=True,
    )

    assert isinstance(result, ExtendedDict)
    assert isinstance(result["service"], ExtendedDict)
    assert isinstance(result["service"]["name"], ExtendedString)
    assert isinstance(result["ports"], ExtendedList)


def test_unwrap_raw_data_from_import_can_return_extended_raw_strings() -> None:
    """Raw imports can opt into ExtendedString."""
    result = unwrap_raw_data_from_import("plain text", encoding="raw", as_extended=True)

    assert isinstance(result, ExtendedString)
    assert result.upper_first() == "Plain text"
