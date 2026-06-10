"""This module provides utilities for handling YAML data.

It includes custom loaders, dumpers, and utility functions for working with YAML.
"""

from __future__ import annotations

from extended_data.yaml_utils.constructors import (
    yaml_construct_pairs,
    yaml_construct_undefined,
)
from extended_data.yaml_utils.dumpers import PureDumper
from extended_data.yaml_utils.loaders import PureLoader
from extended_data.yaml_utils.representers import (
    yaml_literal_str_representer,
    yaml_represent_pairs,
    yaml_represent_tagged,
    yaml_str_representer,
)
from extended_data.yaml_utils.tag_classes import (
    LiteralScalarString,
    YamlPairs,
    YamlTagged,
)
from extended_data.yaml_utils.utils import decode_yaml, encode_yaml, is_yaml_data


__all__ = [
    "LiteralScalarString",
    "PureDumper",
    "PureLoader",
    "YamlPairs",
    "YamlTagged",
    "decode_yaml",
    "encode_yaml",
    "is_yaml_data",
    "yaml_construct_pairs",
    "yaml_construct_undefined",
    "yaml_literal_str_representer",
    "yaml_represent_pairs",
    "yaml_represent_tagged",
    "yaml_str_representer",
]
