"""This module provides utilities for exporting raw data in various formats."""

from __future__ import annotations

import datetime
import pathlib

from collections.abc import Mapping
from typing import Any

from extended_data.containers.factory import to_builtin
from extended_data.primitives.formats.hcl import encode_hcl2
from extended_data.primitives.formats.json import encode_json
from extended_data.primitives.formats.toml import encode_toml
from extended_data.primitives.formats.yaml import (
    LiteralScalarString,
    YamlPairs,
    YamlTagged,
    encode_yaml,
    is_yaml_data,
)
from extended_data.primitives.serialization import normalize_data_encoding
from extended_data.primitives.types import convert_special_types, string_to_bool


def wrap_raw_data_for_export(
    raw_data: Mapping[str, Any] | Any,
    allow_encoding: bool | str = True,
    **format_opts: Any,
) -> str:
    """Wraps raw data for export, optionally encoding it.

    Args:
        raw_data (Mapping[str, Any] | Any): The raw data to wrap.
        allow_encoding (bool | str): The encoding format or flag (default is 'yaml').
        format_opts (Any): Additional options for formatting the output.

    Returns:
        str: The wrapped and encoded data.

    Raises:
        ValueError: If an invalid or unsupported encoding is provided.
    """
    export_data = to_builtin(raw_data)
    contains_yaml_data = is_yaml_data(export_data)
    converted_data = convert_special_types(export_data)

    # Check if allow_encoding is a string specifying the format
    if isinstance(allow_encoding, str):
        allow_encoding_lower = normalize_data_encoding(allow_encoding)
        if allow_encoding_lower == "yaml":
            return encode_yaml(make_raw_data_export_safe(export_data, export_to_yaml=True))
        if allow_encoding_lower == "json":
            return encode_json(converted_data, **format_opts)
        if allow_encoding_lower == "toml":
            return encode_toml(converted_data)
        if allow_encoding_lower == "hcl":
            return encode_hcl2(converted_data)
        if allow_encoding_lower == "raw":
            return str(converted_data)

        # Attempt to convert string-based allow_encoding to a boolean
        try:
            allow_encoding_bool = string_to_bool(allow_encoding, raise_on_error=True)
            allow_encoding = allow_encoding_bool if isinstance(allow_encoding_bool, bool) else allow_encoding
        except ValueError as e:
            raise ValueError(f"Invalid allow_encoding value: {allow_encoding}") from e

    # Determine the encoding based on boolean allow_encoding and YAML data check
    if allow_encoding:
        if contains_yaml_data:
            return encode_yaml(make_raw_data_export_safe(export_data, export_to_yaml=True))
        # Call encode_json with options unpacked to ensure they are correctly passed
        return encode_json(converted_data, **format_opts)

    # If no encoding is allowed, return the string representation of raw_data
    return str(converted_data)


def make_raw_data_export_safe(raw_data: Any, export_to_yaml: bool = False) -> Any:
    r"""Make raw data safe for export by converting complex types to primitives.

    Recursively processes data structures (dicts, lists, sets, tuples, frozensets) and converts:
    - datetime.date/datetime.datetime → ISO format strings
    - pathlib.Path → strings
    - For YAML export: applies special string formatting for GitHub Actions syntax

    Args:
        raw_data: The data to make export-safe (dict, list, set, tuple, frozenset, or primitive).
                  Sets, tuples, and frozensets are converted to lists.
        export_to_yaml: If True, apply YAML-specific formatting (e.g., literal strings for multiline)

    Returns:
        Export-safe version of the data with all complex types converted

    Examples:
        >>> from datetime import datetime
        >>> from pathlib import Path
        >>> data = {"date": datetime(2025, 1, 1), "path": Path("/tmp")}
        >>> make_raw_data_export_safe(data)
        {'date': '2025-01-01T00:00:00', 'path': '/tmp'}

        >>> multiline = {"script": "echo 'line1'\\necho 'line2'"}
        >>> result = make_raw_data_export_safe(multiline, export_to_yaml=True)
        >>> type(result["script"]).__name__
        'LiteralScalarString'
    """
    raw_data = to_builtin(raw_data)

    if export_to_yaml and isinstance(raw_data, YamlTagged):
        return YamlTagged(
            raw_data.tag,
            make_raw_data_export_safe(raw_data.__wrapped__, export_to_yaml=export_to_yaml),
        )
    if export_to_yaml and isinstance(raw_data, YamlPairs):
        return YamlPairs(
            [
                tuple(make_raw_data_export_safe(item, export_to_yaml=export_to_yaml) for item in pair)
                for pair in raw_data
            ]
        )
    if isinstance(raw_data, Mapping):
        return {k: make_raw_data_export_safe(v, export_to_yaml=export_to_yaml) for k, v in raw_data.items()}
    if isinstance(raw_data, (set, list, tuple, frozenset)):
        return [make_raw_data_export_safe(v, export_to_yaml=export_to_yaml) for v in raw_data]

    exported_data = raw_data

    # Convert datetime objects to ISO format strings
    if isinstance(exported_data, (datetime.date, datetime.datetime)):
        exported_data = exported_data.isoformat()
    # Convert Path objects to strings
    elif isinstance(exported_data, pathlib.Path):
        exported_data = str(exported_data)

    # Apply YAML-specific formatting if needed
    if not export_to_yaml or not isinstance(exported_data, str):
        return exported_data

    # Escape GitHub Actions syntax by removing spaces inside expressions
    # This prevents accidental evaluation: "${{ secrets.TOKEN }}" → "${{secrets.TOKEN}}"
    # Note: This is a simple heuristic that handles the most common case.
    # For complete literal output, consider wrapping in quotes at the YAML level.
    exported_data = exported_data.replace("${{ ", "${{").replace(" }}", "}}")

    # Use literal string format for multiline or command strings
    if len(exported_data.splitlines()) > 1 or "||" in exported_data or "&&" in exported_data:
        return LiteralScalarString(exported_data)

    return exported_data
