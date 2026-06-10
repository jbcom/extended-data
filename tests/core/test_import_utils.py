"""Tests for import utility helpers."""

from __future__ import annotations

import pytest

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
