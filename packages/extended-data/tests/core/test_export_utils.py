"""This module contains test functions for verifying the functionality of wrapping raw YAML data for export using the
`extended_data` package. It includes fixtures for simple and complex YAML data and tests for ensuring the proper
encoding and wrapping of this data.

Fixtures:
    - simple_yaml_fixture: Provides a simple YAML string for testing.
    - complex_yaml_fixture: Provides a complex YAML string representing an AWS CloudFormation template for testing.

Functions:
    - test_wrap_raw_data_for_export_yaml: Tests wrapping and encoding of simple YAML data.
    - test_wrap_raw_data_for_export_yaml_complex: Tests wrapping and encoding of complex YAML data.
"""

from __future__ import annotations

import datetime
import json
import pathlib

from collections import defaultdict

import pytest

from extended_data.io.exporters import (
    make_raw_data_export_safe,
    wrap_raw_data_for_export,
)
from extended_data.primitives.formats.yaml import (
    LiteralScalarString,
    YamlPairs,
    YamlTagged,
    decode_yaml,
)


@pytest.fixture
def simple_yaml_fixture() -> str:
    """Provides a simple YAML string for testing.

    Returns:
        str: A simple YAML string.
    """
    return "test_key: test_value\nnested:\n  key1: value1\n  key2: value2\nlist:\n  - item1\n  - item2\n"


@pytest.fixture
def complex_yaml_fixture() -> str:
    """Provides a complex YAML string representing an AWS CloudFormation template for testing.

    Returns:
        str: A complex YAML string.
    """
    return """
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  MyBucket:
    Type: 'AWS::S3::Bucket'
    Properties:
      BucketName: !Sub '${AWS::StackName}-bucket'
      Tags:
        - Key: Name
          Value: !Ref 'AWS::StackName'
Outputs:
  BucketName:
    Value: !Ref MyBucket
    Description: Name of the bucket
"""


def test_wrap_raw_data_for_export_yaml(simple_yaml_fixture: str) -> None:
    """Tests wrapping and encoding of simple YAML data.

    Args:
        simple_yaml_fixture (str): A simple YAML string provided by the fixture.

    Asserts:
        The result of wrap_raw_data_for_export contains key parts of the original YAML string.
    """
    result = wrap_raw_data_for_export(
        decode_yaml(simple_yaml_fixture),
        allow_encoding="yaml",
    )
    assert "test_key: test_value" in result
    assert "key1: value1" in result


def test_wrap_raw_data_for_export_yaml_complex(complex_yaml_fixture: str) -> None:
    """Tests wrapping and encoding of complex YAML data.

    Args:
        complex_yaml_fixture (str): A complex YAML string provided by the fixture.

    Asserts:
        The result of wrap_raw_data_for_export contains key parts of the original YAML string.
    """
    result = wrap_raw_data_for_export(
        decode_yaml(complex_yaml_fixture),
        allow_encoding="yaml",
    )
    assert 'AWSTemplateFormatVersion: "2010-09-09"' in result
    assert 'Type: "AWS::S3::Bucket"' in result


def test_wrap_raw_data_for_export_hcl() -> None:
    """Tests wrapping Terraform-style data as HCL."""
    result = wrap_raw_data_for_export(
        {"locals": [{"region": "us-east-1"}]},
        allow_encoding="hcl",
    )
    assert "locals {" in result
    assert 'region = "us-east-1"' in result


def test_wrap_raw_data_for_export_tf_alias() -> None:
    """Treat Terraform aliases as HCL during export."""
    result = wrap_raw_data_for_export(
        {"locals": [{"region": "us-east-1"}]},
        allow_encoding="tf",
    )
    assert "locals {" in result
    assert 'region = "us-east-1"' in result


def test_wrap_raw_data_for_export_toml() -> None:
    """Encode mappings as TOML when explicitly requested."""
    result = wrap_raw_data_for_export(
        {"package": {"name": "extended-data"}},
        allow_encoding="toml",
    )
    assert "[package]" in result
    assert 'name = "extended-data"' in result


def test_wrap_raw_data_for_export_json_preserves_composite_structure() -> None:
    """JSON export should structurally normalize tuples and frozensets."""
    result = wrap_raw_data_for_export(
        {
            "items": ("a", "b"),
            "values": frozenset([1, 2]),
        },
        allow_encoding="json",
    )
    decoded = json.loads(result)
    assert decoded["items"] == ["a", "b"]
    assert sorted(decoded["values"]) == [1, 2]


def test_wrap_raw_data_for_export_raw_false_and_invalid_values() -> None:
    """Cover raw output, boolean-like strings, and invalid encoding values."""
    raw_data = {"key": "value"}

    assert wrap_raw_data_for_export(raw_data, allow_encoding="raw") == str(raw_data)
    assert wrap_raw_data_for_export(raw_data, allow_encoding="false") == str(raw_data)

    with pytest.raises(ValueError, match="Invalid allow_encoding value: xml"):
        wrap_raw_data_for_export(raw_data, allow_encoding="xml")


def test_wrap_raw_data_for_export_redacts_invalid_encoding_value() -> None:
    """Invalid export-option diagnostics should not echo secret-bearing values."""
    with pytest.raises(ValueError) as exc_info:
        wrap_raw_data_for_export({}, allow_encoding="password=hunter2 Authorization: Bearer raw_token")

    message = str(exc_info.value)
    assert "hunter2" not in message
    assert "raw_token" not in message
    assert "[REDACTED]" in message


def test_wrap_raw_data_for_export_boolean_string_preserves_yaml_native_data() -> None:
    """Auto-encoding should keep YAML-native tagged values in YAML form."""
    raw_data = {"bucket_name": YamlTagged("!Ref", "BucketName")}
    result = wrap_raw_data_for_export(raw_data, allow_encoding="true")
    assert "!Ref" in result
    assert decode_yaml(result) == raw_data


def test_make_raw_data_export_safe_handles_mapping_subclasses() -> None:
    """Normalize nested values even when the input mapping is not a plain dict."""
    data = defaultdict(dict)
    data["config"]["path"] = pathlib.Path("/tmp/demo")

    result = make_raw_data_export_safe(data)

    assert result == {"config": {"path": "/tmp/demo"}}


def test_make_raw_data_export_safe_tuple_with_datetime() -> None:
    """Tests that tuples containing datetime objects are properly converted.

    Asserts:
        - Tuples are converted to lists
        - datetime objects within tuples are converted to ISO format strings
        - The result can be serialized to JSON
    """
    test_date = datetime.date(2025, 1, 15)
    test_datetime = datetime.datetime(2025, 1, 15, 12, 30, 45)

    data = {
        "tuple_with_dates": (test_date, test_datetime, "string"),
        "nested": {"tuple_dates": (test_date, test_datetime)},
    }

    result = make_raw_data_export_safe(data)

    # Check that tuples were converted to lists
    assert isinstance(result["tuple_with_dates"], list)
    assert isinstance(result["nested"]["tuple_dates"], list)

    # Check that datetime objects were converted to strings
    assert result["tuple_with_dates"][0] == "2025-01-15"
    assert result["tuple_with_dates"][1] == "2025-01-15T12:30:45"
    assert result["tuple_with_dates"][2] == "string"

    assert result["nested"]["tuple_dates"][0] == "2025-01-15"
    assert result["nested"]["tuple_dates"][1] == "2025-01-15T12:30:45"

    # Verify JSON serialization works
    json_str = json.dumps(result)
    assert json_str is not None


def test_make_raw_data_export_safe_tuple_with_path() -> None:
    """Tests that tuples containing Path objects are properly converted.

    Asserts:
        - Tuples are converted to lists
        - Path objects within tuples are converted to strings
        - The result can be serialized to JSON
    """
    path1 = pathlib.Path("/tmp/file1.txt")
    path2 = pathlib.Path("/home/user/file2.txt")

    data = {
        "tuple_with_paths": (path1, path2, "regular_string"),
        "list_of_tuples": [(path1, "item1"), (path2, "item2")],
    }

    result = make_raw_data_export_safe(data)

    # Check that tuples were converted to lists
    assert isinstance(result["tuple_with_paths"], list)
    assert isinstance(result["list_of_tuples"][0], list)
    assert isinstance(result["list_of_tuples"][1], list)

    # Check that Path objects were converted to strings
    assert result["tuple_with_paths"][0] == "/tmp/file1.txt"
    assert result["tuple_with_paths"][1] == "/home/user/file2.txt"
    assert result["tuple_with_paths"][2] == "regular_string"

    assert result["list_of_tuples"][0][0] == "/tmp/file1.txt"
    assert result["list_of_tuples"][0][1] == "item1"
    assert result["list_of_tuples"][1][0] == "/home/user/file2.txt"
    assert result["list_of_tuples"][1][1] == "item2"

    # Verify JSON serialization works
    json_str = json.dumps(result)
    assert json_str is not None


def test_make_raw_data_export_safe_tuple_mixed_types() -> None:
    """Tests that tuples with mixed complex types are properly converted.

    Asserts:
        - Tuples with datetime, Path, and regular types are all converted properly
        - Nested tuples are handled correctly
    """
    test_date = datetime.date(2025, 1, 15)
    test_path = pathlib.Path("/tmp/test.txt")

    data = {
        "mixed_tuple": (test_date, test_path, 42, "string", 3.14),
        "nested_tuples": ((test_date, test_path), (1, 2, 3)),
    }

    result = make_raw_data_export_safe(data)

    # Check outer tuple conversion
    assert isinstance(result["mixed_tuple"], list)
    assert result["mixed_tuple"][0] == "2025-01-15"
    assert result["mixed_tuple"][1] == "/tmp/test.txt"
    assert result["mixed_tuple"][2] == 42
    assert result["mixed_tuple"][3] == "string"
    assert result["mixed_tuple"][4] == 3.14

    # Check nested tuple conversion
    assert isinstance(result["nested_tuples"], list)
    assert isinstance(result["nested_tuples"][0], list)
    assert isinstance(result["nested_tuples"][1], list)
    assert result["nested_tuples"][0][0] == "2025-01-15"
    assert result["nested_tuples"][0][1] == "/tmp/test.txt"
    assert result["nested_tuples"][1] == [1, 2, 3]

    # Verify JSON serialization works
    json_str = json.dumps(result)
    assert json_str is not None


def test_make_raw_data_export_safe_empty_tuple() -> None:
    """Tests that empty tuples are properly converted to empty lists.

    Asserts:
        - Empty tuples are converted to empty lists
    """
    data = {"empty_tuple": (), "list_with_empty_tuple": [(), 1, 2]}

    result = make_raw_data_export_safe(data)

    assert isinstance(result["empty_tuple"], list)
    assert len(result["empty_tuple"]) == 0
    assert isinstance(result["list_with_empty_tuple"][0], list)
    assert len(result["list_with_empty_tuple"][0]) == 0


def test_make_raw_data_export_safe_preserves_yaml_wrappers() -> None:
    """YAML-native wrappers should be preserved during YAML-safe conversion."""
    raw_data = {
        "tagged": YamlTagged(
            "!Sub",
            {
                "path": pathlib.Path("/tmp/template.yml"),
                "created": datetime.date(2025, 1, 15),
            },
        ),
        "pairs": YamlPairs(
            [
                (
                    "bucket",
                    YamlTagged("!Ref", "BucketName"),
                )
            ]
        ),
    }

    result = make_raw_data_export_safe(raw_data, export_to_yaml=True)

    assert isinstance(result["tagged"], YamlTagged)
    assert result["tagged"].tag == "!Sub"
    assert result["tagged"].__wrapped__["path"] == "/tmp/template.yml"
    assert result["tagged"].__wrapped__["created"] == "2025-01-15"

    assert isinstance(result["pairs"], YamlPairs)
    pair_key, pair_value = result["pairs"][0]
    assert pair_key == "bucket"
    assert isinstance(pair_value, YamlTagged)
    assert pair_value.tag == "!Ref"
    assert pair_value.__wrapped__ == "BucketName"


def test_make_raw_data_export_safe_frozenset_with_datetime() -> None:
    """Tests that frozensets containing datetime objects are properly converted.

    Asserts:
        - Frozensets are converted to lists
        - datetime objects within frozensets are converted to ISO format strings
        - The result can be serialized to JSON
    """
    test_date = datetime.date(2025, 1, 15)
    test_datetime = datetime.datetime(2025, 1, 15, 12, 30, 45)

    data = {
        "frozenset_with_dates": frozenset([test_date, test_datetime]),
        "nested": {"frozenset_dates": frozenset([test_date])},
    }

    result = make_raw_data_export_safe(data)

    # Check that frozensets were converted to lists
    assert isinstance(result["frozenset_with_dates"], list)
    assert isinstance(result["nested"]["frozenset_dates"], list)

    # Check that datetime objects were converted to strings
    assert "2025-01-15" in result["frozenset_with_dates"]
    assert "2025-01-15T12:30:45" in result["frozenset_with_dates"]
    assert result["nested"]["frozenset_dates"][0] == "2025-01-15"


def test_make_raw_data_export_safe_yaml_string_formatting() -> None:
    """Apply YAML-safe string escaping and literal scalar conversion."""
    result = make_raw_data_export_safe(
        {
            "expr": "${{ secrets.TOKEN }}",
            "script": "echo start && echo done",
        },
        export_to_yaml=True,
    )

    assert result["expr"] == "${{secrets.TOKEN}}"
    assert isinstance(result["script"], LiteralScalarString)
    assert str(result["script"]) == "echo start && echo done"


def test_make_raw_data_export_safe_frozenset_with_path() -> None:
    """Tests that frozensets containing Path objects are properly converted.

    Asserts:
        - Frozensets are converted to lists
        - Path objects within frozensets are converted to strings
        - The result can be serialized to JSON
    """
    path1 = pathlib.Path("/tmp/file1.txt")
    path2 = pathlib.Path("/home/user/file2.txt")

    data = {
        "frozenset_with_paths": frozenset([path1, path2]),
    }

    result = make_raw_data_export_safe(data)

    # Check that frozenset was converted to list
    assert isinstance(result["frozenset_with_paths"], list)

    # Check that Path objects were converted to strings
    assert "/tmp/file1.txt" in result["frozenset_with_paths"]
    assert "/home/user/file2.txt" in result["frozenset_with_paths"]

    # Verify JSON serialization works
    json_str = json.dumps(result)
    assert json_str is not None
