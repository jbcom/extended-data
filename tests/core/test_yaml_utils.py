"""This module contains test functions for verifying the functionality of YAML encoding and decoding using the
`extended_data` package. It includes fixtures for simple and complex YAML data, and tests for encoding,
decoding, and handling custom YAML tags and pairs.

Fixtures:
    - simple_yaml_fixture: Provides a simple YAML string for testing.
    - complex_yaml_fixture: Provides a complex YAML string representing an AWS CloudFormation template for testing.

Functions:
    - test_encode_yaml: Tests encoding of YAML data to string format.
    - test_yaml_construct_undefined: Tests decoding of YAML data with a custom tag.
    - test_yaml_represent_tagged: Tests encoding of YAMLTagged data to string format.
    - test_yaml_pairs_representation: Tests encoding of YamlPairs data to string format.
    - test_decode_and_encode_complex_yaml: Tests decoding and encoding of complex YAML data.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from yaml import MappingNode, ScalarNode, SequenceNode

from extended_data.primitives.formats.errors import DataDecodeError
from extended_data.primitives.formats.yaml import (
    LiteralScalarString,
    YamlPairs,
    YamlTagged,
    decode_yaml,
    encode_yaml,
    is_yaml_data,
    yaml_construct_pairs,
    yaml_construct_undefined,
    yaml_literal_str_representer,
    yaml_represent_pairs,
    yaml_represent_tagged,
    yaml_str_representer,
)


CUSTOM_TAG_VALUE = 12345


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


def test_encode_yaml(simple_yaml_fixture: str) -> None:
    """Tests encoding of YAML data to string format.

    Args:
        simple_yaml_fixture (str): A simple YAML string provided by the fixture.

    Asserts:
        The encoded and then decoded data matches the original data.
    """
    data = decode_yaml(simple_yaml_fixture)
    result = encode_yaml(data)
    expected_data = decode_yaml(simple_yaml_fixture)
    result_data = decode_yaml(result)
    assert result_data == expected_data


def test_yaml_construct_undefined() -> None:
    """Tests decoding of YAML data with a custom tag.

    Asserts:
        The decoded data is an instance of YamlTagged with the expected tag and values.
    """
    custom_tag_yaml_fixture = "!CustomTag\nname: custom\nvalue: 12345\n"
    data = decode_yaml(custom_tag_yaml_fixture)
    assert isinstance(data, YamlTagged)
    assert data.tag == "!CustomTag"
    assert data["name"] == "custom"
    assert data["value"] == CUSTOM_TAG_VALUE


def test_yaml_represent_tagged() -> None:
    """Tests encoding of YamlTagged data to string format.

    Asserts:
        The encoded string contains the custom tag and the expected key-value pairs.
    """
    data = YamlTagged("!CustomTag", {"name": "custom", "value": CUSTOM_TAG_VALUE})
    encoded_data = encode_yaml(data)
    assert "!CustomTag" in encoded_data
    assert "name: custom" in encoded_data
    assert f"value: {CUSTOM_TAG_VALUE}" in encoded_data


def test_yaml_pairs_representation() -> None:
    """Tests encoding of YamlPairs data to string format.

    Asserts:
        The encoded string contains the expected key-value pairs.
    """
    data = YamlPairs([("key1", "value1"), ("key2", "value2")])
    encoded_data = encode_yaml(data)
    assert "key1: value1" in encoded_data
    assert "key2: value2" in encoded_data


def test_decode_and_encode_complex_yaml(complex_yaml_fixture: str) -> None:
    """Tests decoding and encoding of complex YAML data.

    Args:
        complex_yaml_fixture (str): A complex YAML string provided by the fixture.

    Asserts:
        The encoded string contains key elements of the original YAML string.
    """
    data = decode_yaml(complex_yaml_fixture)
    assert isinstance(data, dict), f"Expected dict, but got {type(data)}"
    encoded_data = encode_yaml(data)
    assert "AWSTemplateFormatVersion" in encoded_data
    assert "Resources" in encoded_data
    assert "Outputs" in encoded_data


def test_decode_yaml_bytes_success(simple_yaml_fixture: str) -> None:
    """Decode YAML from bytes."""
    result = decode_yaml(simple_yaml_fixture.encode("utf-8"))
    assert result["test_key"] == "test_value"


def test_decode_yaml_invalid_bytes() -> None:
    """Raise a sanitized decode error when bytes cannot be decoded."""
    with pytest.raises(DataDecodeError, match="input bytes are not valid UTF-8"):
        decode_yaml(b"\x80")


def test_decode_yaml_invalid_input_does_not_echo_payload() -> None:
    """Invalid YAML messages do not include source snippets."""
    with pytest.raises(DataDecodeError) as exc_info:
        decode_yaml("token: [super-secret")

    message = str(exc_info.value)
    assert "Failed to decode YAML data" in message
    assert "line 1" in message
    assert "super-secret" not in message


@pytest.mark.parametrize(
    ("node", "loader_method", "constructed_value"),
    [
        (ScalarNode("!CustomTag", "hello"), "construct_scalar", "hello"),
        (
            SequenceNode("!CustomTag", [ScalarNode("tag:yaml.org,2002:int", "1")]),
            "construct_sequence",
            [1],
        ),
        (
            MappingNode(
                "!CustomTag",
                [(ScalarNode("tag:yaml.org,2002:str", "name"), ScalarNode("tag:yaml.org,2002:str", "value"))],
            ),
            "construct_mapping",
            {"name": "value"},
        ),
    ],
)
def test_yaml_construct_undefined_handles_supported_nodes(
    mocker,
    node: ScalarNode | SequenceNode | MappingNode,
    loader_method: str,
    constructed_value: object,
) -> None:
    """Construct tagged values for scalar, sequence, and mapping nodes."""
    loader = mocker.Mock()
    getattr(loader, loader_method).return_value = constructed_value

    result = yaml_construct_undefined(loader, node)

    assert isinstance(result, YamlTagged)
    assert result.tag == "!CustomTag"
    assert result.__wrapped__ == constructed_value


def test_yaml_construct_undefined_rejects_unexpected_node_type(mocker) -> None:
    """Reject unknown YAML node implementations."""
    with pytest.raises(TypeError, match="Unexpected node type: object"):
        yaml_construct_undefined(mocker.Mock(), object())


def test_yaml_construct_pairs_returns_dict_for_hashable_keys(mocker) -> None:
    """Construct regular mappings when keys are hashable."""
    loader = mocker.Mock()
    loader.construct_pairs.return_value = [("key", "value")]

    result = yaml_construct_pairs(loader, MappingNode("tag:yaml.org,2002:map", []))

    assert result == {"key": "value"}


def test_yaml_construct_pairs_returns_yaml_pairs_for_unhashable_keys(mocker) -> None:
    """Preserve pairs when keys cannot be converted to a dict."""
    loader = mocker.Mock()
    loader.construct_pairs.return_value = [(["key"], "value")]

    result = yaml_construct_pairs(loader, MappingNode("tag:yaml.org,2002:map", []))

    assert isinstance(result, YamlPairs)
    assert result == [(["key"], "value")]


def test_yaml_represent_tagged_sets_tag(mocker) -> None:
    """Propagate custom tags onto the represented node."""
    represented = SimpleNamespace(tag=None)
    dumper = mocker.Mock()
    dumper.represent_data.return_value = represented

    result = yaml_represent_tagged(dumper, YamlTagged("!CustomTag", {"name": "value"}))

    assert result is represented
    assert result.tag == "!CustomTag"
    dumper.represent_data.assert_called_once_with({"name": "value"})


def test_yaml_represent_tagged_rejects_non_tagged(mocker) -> None:
    """Reject invalid tagged representation inputs."""
    with pytest.raises(TypeError, match="Expected YamlTagged, got dict"):
        yaml_represent_tagged(mocker.Mock(), {"name": "value"})


def test_yaml_represent_pairs_uses_represent_dict(mocker) -> None:
    """Represent YAML pairs through the dumper."""
    dumper = mocker.Mock()
    dumper.represent_dict.return_value = {"kind": "mapping"}

    result = yaml_represent_pairs(dumper, YamlPairs([("key", "value")]))

    assert result == {"kind": "mapping"}
    dumper.represent_dict.assert_called_once_with(YamlPairs([("key", "value")]))


def test_yaml_represent_pairs_rejects_non_pairs(mocker) -> None:
    """Reject invalid pair representation inputs."""
    with pytest.raises(TypeError, match="Expected YamlPairs, got list"):
        yaml_represent_pairs(mocker.Mock(), [("key", "value")])


@pytest.mark.parametrize(
    ("data", "expected_style"),
    [
        ("line1\nline2", "|"),
        ("key: value", '"'),
        ("plain string", None),
    ],
)
def test_yaml_str_representer_styles_strings(mocker, data: str, expected_style: str | None) -> None:
    """Choose YAML string styles based on content."""
    dumper = mocker.Mock()
    sentinel = object()
    dumper.represent_scalar.return_value = sentinel

    result = yaml_str_representer(dumper, data)

    assert result is sentinel
    if expected_style is None:
        dumper.represent_scalar.assert_called_once_with("tag:yaml.org,2002:str", data)
    else:
        dumper.represent_scalar.assert_called_once_with("tag:yaml.org,2002:str", data, style=expected_style)


def test_yaml_literal_str_representer_uses_literal_style(mocker) -> None:
    """Always emit literal scalar strings using block style."""
    dumper = mocker.Mock()
    sentinel = object()
    dumper.represent_scalar.return_value = sentinel

    result = yaml_literal_str_representer(dumper, LiteralScalarString("echo one\necho two"))

    assert result is sentinel
    dumper.represent_scalar.assert_called_once_with(
        "tag:yaml.org,2002:str",
        "echo one\necho two",
        style="|",
    )


def test_is_yaml_data_detects_nested_tagged_values() -> None:
    """Detect tagged YAML content inside nested structures."""
    data = {"resource": [{"name": YamlTagged("!Ref", "BucketName")}]}
    assert is_yaml_data(data) is True
    assert is_yaml_data({"resource": [{"name": "BucketName"}]}) is False


def test_is_yaml_data_detects_yaml_pairs_and_tuples() -> None:
    """Treat YAML pair collections and tuple-contained tags as YAML-native data."""
    assert is_yaml_data(YamlPairs([("name", "value")])) is True
    assert is_yaml_data((YamlTagged("!Ref", "BucketName"),)) is True
