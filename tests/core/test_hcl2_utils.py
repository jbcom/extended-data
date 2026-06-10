"""Tests for HCL2 encoding and decoding helpers."""

from __future__ import annotations

import pytest

from lark.exceptions import ParseError, UnexpectedToken

from extended_data import hcl2_utils
from extended_data.hcl2_utils import decode_hcl2, encode_hcl2


@pytest.fixture
def resource_hcl() -> str:
    """Provide a representative Terraform resource block."""
    return """
    resource "aws_s3_bucket" "b" {
      bucket = "my-tf-test-bucket"
      acl    = "private"

      tags = {
        Name        = "My bucket"
        Environment = "Dev"
      }
    }
    """


@pytest.fixture
def expected_resource_data() -> dict[str, object]:
    """Provide the normalized plain-Python resource structure."""
    return {
        "resource": [
            {
                "aws_s3_bucket": {
                    "b": {
                        "bucket": "my-tf-test-bucket",
                        "acl": "private",
                        "tags": {"Name": "My bucket", "Environment": "Dev"},
                    },
                },
            },
        ],
    }


def test_decode_hcl2_valid(resource_hcl: str, expected_resource_data: dict[str, object]) -> None:
    """Decode a Terraform block into normalized plain Python data."""
    assert decode_hcl2(resource_hcl) == expected_resource_data


def test_decode_hcl2_empty() -> None:
    """Decode empty HCL into an empty mapping."""
    assert decode_hcl2("") == {}


def test_decode_hcl2_invalid() -> None:
    """Reject invalid HCL input."""
    with pytest.raises(UnexpectedToken):
        decode_hcl2("invalid hcl2 data")


def test_decode_hcl2_invalid_bytes() -> None:
    """Reject byte input that cannot be decoded as UTF-8."""
    with pytest.raises(ParseError, match="Failed to decode bytes to string"):
        decode_hcl2(b"\x80")


def test_decode_hcl2_normalizes_quoted_strings_and_expressions() -> None:
    """Strip parser-added quotes while leaving expressions as strings."""
    hcl_data = """
    locals {
      rendered = "${var.project_name}"
      resolved = var.project_name
      values   = ["hello", var.environment]
    }
    """

    decoded = decode_hcl2(hcl_data)

    assert decoded == {
        "locals": [
            {
                "rendered": "${var.project_name}",
                "resolved": "${var.project_name}",
                "values": ["hello", "${var.environment}"],
            },
        ],
    }


def test_normalize_hcl_value_removes_metadata_and_parser_quotes() -> None:
    """Normalize nested parser artifacts into plain Python values."""
    normalized = hcl2_utils._normalize_hcl_value(
        {
            '"name"': '"value"',
            "__is_block__": True,
            "nested": [{'"inner"': '"item"'}],
        }
    )

    assert normalized == {
        "name": "value",
        "nested": [{"inner": "item"}],
    }


def test_normalize_hcl_value_preserves_quoted_metadata_like_keys() -> None:
    """Treat quoted metadata-shaped keys as user data, not parser artifacts."""
    normalized = hcl2_utils._normalize_hcl_value(
        {
            '"__is_block__"': '"kept"',
            "__is_block__": True,
        }
    )

    assert normalized == {"__is_block__": "kept"}


def test_strip_hcl_parser_quotes_handles_invalid_json_literal() -> None:
    """Fall back to slicing when a quoted parser string is not valid JSON."""
    assert hcl2_utils._strip_hcl_parser_quotes(r'"\q"') == r"\q"


def test_encode_hcl2_round_trips_supported_contract(expected_resource_data: dict[str, object]) -> None:
    """Encode supported Terraform-style data and decode it back."""
    encoded = encode_hcl2(expected_resource_data)

    assert 'resource "aws_s3_bucket" "b" {' in encoded
    assert 'bucket = "my-tf-test-bucket"' in encoded
    assert "tags = {" in encoded
    assert decode_hcl2(encoded) == expected_resource_data


def test_encode_hcl2_handles_scalars_and_unlabelled_blocks() -> None:
    """Encode common Terraform scalar values and unlabeled blocks."""
    data = {
        "terraform": [{"required_version": ">= 1.8.0"}],
        "locals": [{"enabled": True, "count": 2, "threshold": 1.5, "empty": None}],
    }

    encoded = encode_hcl2(data)

    assert "terraform {" in encoded
    assert 'required_version = ">= 1.8.0"' in encoded
    assert "enabled = true" in encoded
    assert "count = 2" in encoded
    assert "threshold = 1.5" in encoded
    assert "empty = null" in encoded
    assert decode_hcl2(encoded) == data


def test_encode_hcl2_normalizes_tuple_like_collections() -> None:
    """Convert tuple-like collections to HCL lists before serialization."""
    data = {
        "locals": [
            {
                "items": ("alpha", "beta"),
                "values": frozenset([1, 2]),
            }
        ]
    }

    encoded = encode_hcl2(data)

    assert "items = [" in encoded
    assert '"alpha",' in encoded
    assert '"beta",' in encoded
    assert "values = [" in encoded
    assert sorted(decode_hcl2(encoded)["locals"][0]["values"]) == [1, 2]
    assert decode_hcl2(encoded)["locals"][0]["items"] == ["alpha", "beta"]


def test_encode_hcl2_keeps_list_of_objects_as_attribute_values() -> None:
    """Serialize list-of-object attributes with '=' instead of nested block syntax."""
    data = {
        "locals": [
            {
                "items": [
                    {"name": "alpha"},
                    {"name": "beta"},
                ]
            }
        ]
    }

    encoded = encode_hcl2(data)

    assert "items = [" in encoded
    assert "items {" not in encoded
    assert decode_hcl2(encoded) == data


def test_encode_hcl2_handles_empty_collections_and_generic_labeled_blocks() -> None:
    """Encode empty collection values and inferred generic block labels."""
    data = {
        "locals": [{"settings": {}, "items": []}],
        "custom_block": [{"alpha": {"beta": {"value": 1}}}],
    }

    encoded = encode_hcl2(data)

    assert "settings = {}" in encoded
    assert "items = []" in encoded
    assert 'custom_block "alpha" "beta" {' in encoded
    assert "value = 1" in encoded
    assert decode_hcl2(encoded) == data


def test_encode_hcl2_handles_empty_block_bodies() -> None:
    """Encode blocks that intentionally have no body content."""
    data = {"terraform": [{}]}

    encoded = encode_hcl2(data)

    assert "terraform {" in encoded
    assert decode_hcl2(encoded) == data


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (
            {"resource": [{"aws_s3_bucket": {"bucket": "missing label body"}}]},
            "Block 'resource' expects entries shaped like",
        ),
        (
            {"variable": [{"region": "not-a-body"}]},
            "Block 'variable' expects entries shaped like",
        ),
    ],
)
def test_encode_hcl2_rejects_invalid_block_shapes(data: dict[str, object], message: str) -> None:
    """Reject malformed Terraform block-list entries."""
    with pytest.raises((TypeError, ValueError), match=message):
        encode_hcl2(data)


def test_extract_block_instance_covers_remaining_shape_edges() -> None:
    """Exercise the remaining explicit block-shape branches directly."""
    with pytest.raises(ValueError, match=r"Block 'resource' expects entries shaped like"):
        hcl2_utils._extract_block_instance(
            "resource",
            {"aws_s3_bucket": {"logs": {}, "extra": {}}},
        )

    assert hcl2_utils._extract_block_instance(
        "variable",
        {"region": {"type": "string"}},
    ) == (["region"], {"type": "string"})

    assert hcl2_utils._extract_block_instance(
        "custom_block",
        {"alpha": {"value": 1, "enabled": True}},
    ) == (["alpha"], {"value": 1, "enabled": True})

    assert hcl2_utils._extract_block_instance(
        "custom_block",
        {"alpha": {"beta": {"gamma": {"value": 1}}}},
    ) == (["alpha"], {"beta": {"gamma": {"value": 1}}})


def test_hcl_internal_helpers_cover_scalar_and_trailing_comma_edges() -> None:
    """Exercise remaining scalar and comma helper branches."""
    assert hcl2_utils._is_hcl_identifier("alpha_1") is True
    assert hcl2_utils._is_hcl_identifier("1alpha") is False
    assert hcl2_utils._with_trailing_comma("") == ","
    assert hcl2_utils._with_trailing_comma("value") == "value,"

    with pytest.raises(TypeError, match="Unsupported HCL scalar type: object"):
        hcl2_utils._serialize_hcl_scalar(object())


def test_hcl_block_detection_helpers_distinguish_attribute_object_lists() -> None:
    """Treat known blocks and labeled generic blocks differently from object arrays."""
    assert hcl2_utils._is_hcl_block_list("locals", [{"value": 1}]) is True
    assert hcl2_utils._is_hcl_block_list("items", [{"value": 1}]) is False
    assert hcl2_utils._is_hcl_block_list("custom_block", [{"alpha": {"beta": {"value": 1}}}]) is True
    assert hcl2_utils._looks_like_generic_labeled_block_instance({"alpha": {"beta": {"value": 1}}}) is True
    assert hcl2_utils._looks_like_generic_labeled_block_instance({"alpha": {"value": 1}}) is False
    assert hcl2_utils._looks_like_generic_labeled_block_instance({"alpha": 1, "beta": 2}) is False


def test_extract_block_instance_rejects_non_mapping_entries() -> None:
    """Reject non-mapping values when explicitly extracting block instances."""
    with pytest.raises(TypeError, match=r"Block 'resource' entries must be mappings\."):
        hcl2_utils._extract_block_instance("resource", "invalid")


def test_encode_hcl2_rejects_non_mapping_root() -> None:
    """Reject document roots that are not HCL bodies."""
    with pytest.raises(TypeError, match="mapping at the document root"):
        encode_hcl2(["not", "a", "mapping"])
