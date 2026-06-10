"""Utilities for decoding and encoding HCL2 data."""

from __future__ import annotations

import json

from collections.abc import Mapping
from io import StringIO
from json import JSONDecodeError
from typing import Any

import hcl2

from lark.exceptions import ParseError

from extended_data.primitives.strings import bytestostr
from extended_data.primitives.types import convert_special_types


_HCL_METADATA_KEYS = frozenset({"__is_block__"})
_HCL_ONE_LABEL_BLOCKS = frozenset({"backend", "dynamic", "module", "output", "provider", "provisioner", "variable"})
_HCL_TWO_LABEL_BLOCKS = frozenset({"data", "ephemeral", "resource"})
_HCL_UNLABELED_BLOCKS = frozenset({"locals", "terraform"})
_IDENTIFIER_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
_QUOTED_STRING_MIN_LENGTH = 2


def _is_hcl_identifier(value: str) -> bool:
    """Return whether the given string can be emitted as a bare HCL identifier."""
    if not value or value[0].isdigit() or value[0] == "-":
        return False
    return all(char in _IDENTIFIER_CHARS for char in value)


def _strip_hcl_parser_quotes(value: str) -> str:
    """Remove one parser-added string-literal layer when present."""
    if len(value) >= _QUOTED_STRING_MIN_LENGTH and value[0] == value[-1] == '"':
        try:
            return json.loads(value)
        except JSONDecodeError:
            return value[1:-1]
    return value


def _normalize_hcl_value(value: Any) -> Any:
    """Normalize raw python-hcl2 output into plain Python data."""
    if isinstance(value, str):
        return _strip_hcl_parser_quotes(value)
    if isinstance(value, list):
        return [_normalize_hcl_value(item) for item in value]
    if isinstance(value, Mapping):
        normalized: dict[Any, Any] = {}
        for key, item in value.items():
            normalized_key = _strip_hcl_parser_quotes(key) if isinstance(key, str) else key
            is_quoted_user_key = isinstance(key, str) and key.startswith('"') and key.endswith('"')
            if not is_quoted_user_key and normalized_key in _HCL_METADATA_KEYS:
                continue
            normalized[normalized_key] = _normalize_hcl_value(item)
        return normalized
    return value


def _serialize_hcl_key(key: Any) -> str:
    """Serialize a mapping key for HCL object and attribute contexts."""
    text = str(key)
    return text if _is_hcl_identifier(text) else json.dumps(text)


def _serialize_hcl_label(label: Any) -> str:
    """Serialize a block label as a quoted HCL string."""
    return json.dumps(str(label))


def _serialize_hcl_scalar(value: Any) -> str:
    """Serialize a supported scalar value to HCL."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value)

    message = f"Unsupported HCL scalar type: {type(value).__name__}"
    raise TypeError(message)


def _with_trailing_comma(rendered: str) -> str:
    """Append a trailing comma to the last line of a rendered value."""
    lines = rendered.splitlines()
    if not lines:
        return ","
    lines[-1] = f"{lines[-1]},"
    return "\n".join(lines)


def _mapping_looks_like_block_body(value: Mapping[Any, Any]) -> bool:
    """Heuristically determine whether a mapping is a block body."""
    return not value or any(key in _HCL_METADATA_KEYS or not isinstance(item, Mapping) for key, item in value.items())


def _extract_block_instance(block_name: str, instance: Any) -> tuple[list[str], Mapping[str, Any]]:
    """Extract labels and a body mapping from a block-list item."""
    if not isinstance(instance, Mapping):
        message = f"Block '{block_name}' entries must be mappings."
        raise TypeError(message)

    if block_name in _HCL_TWO_LABEL_BLOCKS and len(instance) == 1:
        label1, nested = next(iter(instance.items()))
        if isinstance(nested, Mapping) and len(nested) == 1:
            label2, body = next(iter(nested.items()))
            if isinstance(body, Mapping):
                return [str(label1), str(label2)], body
        message = f"Block '{block_name}' expects entries shaped like {{label1: {{label2: body}}}}."
        raise ValueError(message)

    if block_name in _HCL_ONE_LABEL_BLOCKS and len(instance) == 1:
        label, body = next(iter(instance.items()))
        if isinstance(body, Mapping):
            return [str(label)], body
        message = f"Block '{block_name}' expects entries shaped like {{label: body}}."
        raise ValueError(message)

    if len(instance) == 1:
        label1, nested = next(iter(instance.items()))
        if isinstance(nested, Mapping):
            if len(nested) == 1:
                label2, body = next(iter(nested.items()))
                if isinstance(body, Mapping) and _mapping_looks_like_block_body(body):
                    return [str(label1), str(label2)], body
            return [str(label1)], nested

    return [], instance


def _looks_like_generic_labeled_block_instance(instance: Any) -> bool:
    """Return whether a generic block item looks like a labeled block."""
    if not isinstance(instance, Mapping) or len(instance) != 1:
        return False

    _, nested = next(iter(instance.items()))
    if not isinstance(nested, Mapping) or len(nested) != 1:
        return False

    _, body = next(iter(nested.items()))
    return isinstance(body, Mapping) and _mapping_looks_like_block_body(body)


def _is_hcl_block_list(block_name: str, value: Any) -> bool:
    """Determine whether a list of mappings should be emitted as HCL blocks."""
    if not isinstance(value, list) or not value or not all(isinstance(item, Mapping) for item in value):
        return False

    if block_name in (_HCL_ONE_LABEL_BLOCKS | _HCL_TWO_LABEL_BLOCKS | _HCL_UNLABELED_BLOCKS):
        return True

    return all(_looks_like_generic_labeled_block_instance(item) for item in value)


def _serialize_hcl_list(values: list[Any], indent_level: int) -> str:
    """Serialize a list value in HCL syntax."""
    if not values:
        return "[]"

    indent = "  " * indent_level
    item_indent = "  " * (indent_level + 1)
    lines = ["["]
    for item in values:
        rendered = _serialize_hcl_value(item, indent_level + 1)
        lines.append(f"{item_indent}{_with_trailing_comma(rendered)}")
    lines.append(f"{indent}]")
    return "\n".join(lines)


def _serialize_hcl_object(mapping: Mapping[str, Any], indent_level: int) -> str:
    """Serialize a mapping as an HCL object value."""
    if not mapping:
        return "{}"

    indent = "  " * indent_level
    child_indent = "  " * (indent_level + 1)
    lines = ["{"]
    for key, value in mapping.items():
        rendered_value = _serialize_hcl_value(value, indent_level + 1)
        lines.append(f"{child_indent}{_serialize_hcl_key(key)} = {rendered_value}")
    lines.append(f"{indent}}}")
    return "\n".join(lines)


def _serialize_hcl_value(value: Any, indent_level: int) -> str:
    """Serialize a supported HCL value."""
    if isinstance(value, Mapping):
        return _serialize_hcl_object(value, indent_level)
    if isinstance(value, list):
        return _serialize_hcl_list(value, indent_level)
    return _serialize_hcl_scalar(value)


def _serialize_hcl_body(mapping: Mapping[str, Any], indent_level: int) -> str:
    """Serialize an HCL body mapping."""
    indent = "  " * indent_level
    lines: list[str] = []
    for key, value in mapping.items():
        if _is_hcl_block_list(str(key), value):
            for item in value:
                labels, body = _extract_block_instance(str(key), item)
                header = " ".join([_serialize_hcl_key(key), *(_serialize_hcl_label(label) for label in labels)])
                lines.append(f"{indent}{header} {{")
                body_text = _serialize_hcl_body(body, indent_level + 1)
                if body_text:
                    lines.extend(body_text.splitlines())
                lines.append(f"{indent}}}")
            continue

        rendered_value = _serialize_hcl_value(value, indent_level)
        lines.append(f"{indent}{_serialize_hcl_key(key)} = {rendered_value}")

    return "\n".join(lines)


def decode_hcl2(hcl2_data: str | memoryview | bytes | bytearray) -> Any:
    """Decodes HCL2 data into a Python object.

    Args:
        hcl2_data (str | memoryview | bytes | bytearray): The HCL2 data to decode.

    Returns:
        Any: The decoded Python object.

    Raises:
        ParseError If the HCL2 data cannot be decoded.
        UnexpectedToken If the HCL2 data cannot be parsed.
    """
    try:
        hcl2_data = bytestostr(hcl2_data)
    except UnicodeDecodeError as exc:
        raise ParseError(f"Failed to decode bytes to string: {hcl2_data!r}") from exc

    hcl2_data_stream = StringIO(hcl2_data)
    return _normalize_hcl_value(hcl2.load(hcl2_data_stream))


def encode_hcl2(data: Any) -> str:
    """Encode plain Terraform-style data into an HCL2 string.

    Args:
        data (Any): The Python object to encode.

    Returns:
        str: The encoded HCL2 string.
    """
    if not isinstance(data, Mapping):
        message = "HCL encoding requires a mapping at the document root."
        raise TypeError(message)

    serialized = _serialize_hcl_body(convert_special_types(data), indent_level=0)
    return serialized.rstrip()
