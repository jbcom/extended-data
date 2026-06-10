"""Tests for serialization format normalization helpers."""

from __future__ import annotations

from extended_data.serialization_utils import normalize_data_encoding


def test_normalize_data_encoding_aliases_and_passthrough() -> None:
    """Normalize supported aliases while lowercasing unknown formats."""
    assert normalize_data_encoding("YML") == "yaml"
    assert normalize_data_encoding("tml") == "toml"
    assert normalize_data_encoding("tfvars") == "hcl"
    assert normalize_data_encoding("TXT") == "raw"
    assert normalize_data_encoding("XML") == "xml"


def test_normalize_data_encoding_none() -> None:
    """Preserve None when no encoding is provided."""
    assert normalize_data_encoding(None) is None
