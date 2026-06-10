"""Extended Data.

This package provides Python utilities for structured data primitives, inputs,
logging, vendor data connectors, and workflow-oriented integrations.
"""

from __future__ import annotations

import importlib

from typing import TYPE_CHECKING, Any

from extended_data._version import __version__
from extended_data.containers import ExtendedDict, ExtendedList, ExtendedSet, ExtendedString, extend_data, to_builtin
from extended_data.io.base64 import base64_decode, base64_encode
from extended_data.io.exporters import (
    make_raw_data_export_safe,
    wrap_raw_data_for_export,
)
from extended_data.io.files import (
    FilePath,
    clone_repository_to_temp,
    decode_file,
    delete_file,
    file_path_depth,
    file_path_rel_to_root,
    get_encoding_for_file_path,
    get_parent_repository,
    get_repository_name,
    get_tld,
    is_url,
    match_file_extensions,
    read_file,
    resolve_local_path,
    write_file,
)
from extended_data.io.importers import unwrap_raw_data_from_import
from extended_data.primitives.formats.errors import DataDecodeError
from extended_data.primitives.formats.hcl import decode_hcl2, encode_hcl2
from extended_data.primitives.formats.json import decode_json, encode_json
from extended_data.primitives.formats.toml import decode_toml, encode_toml
from extended_data.primitives.formats.yaml import decode_yaml, encode_yaml, is_yaml_data
from extended_data.primitives.introspection import (
    filter_methods,
    get_available_methods,
    get_caller,
    get_inputs_from_docstring,
    get_unique_signature,
    update_docstring,
)
from extended_data.primitives.mappings import (
    SortedDefaultDict,
    all_values_from_map,
    create_merger,
    deduplicate_map,
    deep_merge,
    filter_map,
    first_non_empty_value_from_map,
    flatten_map,
    get_default_dict,
    unhump_map,
    zipmap,
)
from extended_data.primitives.matching import is_non_empty_match, is_partial_match
from extended_data.primitives.sequences import filter_list, flatten_list
from extended_data.primitives.splitting import split_dict_by_type, split_list_by_type
from extended_data.primitives.state import (
    all_non_empty,
    all_non_empty_in_dict,
    all_non_empty_in_list,
    any_non_empty,
    are_nothing,
    first_non_empty,
    is_nothing,
    yield_non_empty,
)
from extended_data.primitives.string_transforms import (
    humanize,
    ordinalize,
    pluralize,
    singularize,
    titleize,
    to_camel_case,
    to_kebab_case,
    to_pascal_case,
    to_snake_case,
)
from extended_data.primitives.strings import (
    bytestostr,
    lower_first_char,
    removeprefix,
    removesuffix,
    sanitize_key,
    titleize_name,
    truncate,
    upper_first_char,
)
from extended_data.primitives.types import (
    convert_special_type,
    convert_special_types,
    get_default_value_for_type,
    get_primitive_type_for_instance_type,
    make_hashable,
    reconstruct_special_type,
    reconstruct_special_types,
    strtobool,
    strtodate,
    strtodatetime,
    strtofloat,
    strtoint,
    strtopath,
    strtotime,
    typeof,
)
from extended_data.workflows import DataWorkflow, WorkflowResult, WorkflowStep


if TYPE_CHECKING:
    from extended_data.connectors import (
        ConnectorFabric,
        ConnectorInfo,
        VendorConnectorBase,
        get_connector,
        get_connector_class,
        get_connector_info,
        list_connector_info,
        list_connectors,
    )
    from extended_data.inputs import InputProvider, directed_inputs, input_config
    from extended_data.logging import ExitRunError, KeyTransform, Logging
    from extended_data.secrets import OutputFormat, SecretsConnector, SyncOperation, SyncOptions, SyncResult


_LAZY_EXPORTS = {
    "ConnectorFabric": ("extended_data.connectors", "ConnectorFabric"),
    "ConnectorInfo": ("extended_data.connectors", "ConnectorInfo"),
    "ExitRunError": ("extended_data.logging", "ExitRunError"),
    "InputProvider": ("extended_data.inputs", "InputProvider"),
    "KeyTransform": ("extended_data.logging", "KeyTransform"),
    "Logging": ("extended_data.logging", "Logging"),
    "OutputFormat": ("extended_data.secrets", "OutputFormat"),
    "SecretsConnector": ("extended_data.secrets", "SecretsConnector"),
    "SyncOperation": ("extended_data.secrets", "SyncOperation"),
    "SyncOptions": ("extended_data.secrets", "SyncOptions"),
    "SyncResult": ("extended_data.secrets", "SyncResult"),
    "VendorConnectorBase": ("extended_data.connectors", "VendorConnectorBase"),
    "directed_inputs": ("extended_data.inputs", "directed_inputs"),
    "get_connector": ("extended_data.connectors", "get_connector"),
    "get_connector_class": ("extended_data.connectors", "get_connector_class"),
    "get_connector_info": ("extended_data.connectors", "get_connector_info"),
    "input_config": ("extended_data.inputs", "input_config"),
    "list_connector_info": ("extended_data.connectors", "list_connector_info"),
    "list_connectors": ("extended_data.connectors", "list_connectors"),
}


def __getattr__(name: str) -> Any:
    """Lazily expose integrated subpackage primitives at the package root."""
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attr_name = _LAZY_EXPORTS[name]
    value = getattr(importlib.import_module(module_name), attr_name)
    globals()[name] = value
    return value


__all__ = [
    "ConnectorFabric",
    "ConnectorInfo",
    "DataDecodeError",
    "DataWorkflow",
    "ExitRunError",
    "ExtendedDict",
    "ExtendedList",
    "ExtendedSet",
    "ExtendedString",
    "FilePath",
    "InputProvider",
    "KeyTransform",
    "Logging",
    "OutputFormat",
    "SecretsConnector",
    "SortedDefaultDict",
    "SyncOperation",
    "SyncOptions",
    "SyncResult",
    "VendorConnectorBase",
    "WorkflowResult",
    "WorkflowStep",
    "__version__",
    "all_non_empty",
    "all_non_empty_in_dict",
    "all_non_empty_in_list",
    "all_values_from_map",
    "any_non_empty",
    "are_nothing",
    "base64_decode",
    "base64_encode",
    "bytestostr",
    "clone_repository_to_temp",
    "convert_special_type",
    "convert_special_types",
    "create_merger",
    "decode_file",
    "decode_hcl2",
    "decode_json",
    "decode_toml",
    "decode_yaml",
    "deduplicate_map",
    "deep_merge",
    "delete_file",
    "directed_inputs",
    "encode_hcl2",
    "encode_json",
    "encode_toml",
    "encode_yaml",
    "extend_data",
    "file_path_depth",
    "file_path_rel_to_root",
    "filter_list",
    "filter_map",
    "filter_methods",
    "first_non_empty",
    "first_non_empty_value_from_map",
    "flatten_list",
    "flatten_map",
    "get_available_methods",
    "get_caller",
    "get_connector",
    "get_connector_class",
    "get_connector_info",
    "get_default_dict",
    "get_default_value_for_type",
    "get_encoding_for_file_path",
    "get_inputs_from_docstring",
    "get_parent_repository",
    "get_primitive_type_for_instance_type",
    "get_repository_name",
    "get_tld",
    "get_unique_signature",
    "humanize",
    "input_config",
    "is_non_empty_match",
    "is_nothing",
    "is_partial_match",
    "is_url",
    "is_yaml_data",
    "list_connector_info",
    "list_connectors",
    "lower_first_char",
    "make_hashable",
    "make_raw_data_export_safe",
    "match_file_extensions",
    "ordinalize",
    "pluralize",
    "read_file",
    "reconstruct_special_type",
    "reconstruct_special_types",
    "removeprefix",
    "removesuffix",
    "resolve_local_path",
    "sanitize_key",
    "singularize",
    "split_dict_by_type",
    "split_list_by_type",
    "strtobool",
    "strtodate",
    "strtodatetime",
    "strtofloat",
    "strtoint",
    "strtopath",
    "strtotime",
    "titleize",
    "titleize_name",
    "to_builtin",
    "to_camel_case",
    "to_kebab_case",
    "to_pascal_case",
    "to_snake_case",
    "truncate",
    "typeof",
    "unhump_map",
    "unwrap_raw_data_from_import",
    "update_docstring",
    "upper_first_char",
    "wrap_raw_data_for_export",
    "write_file",
    "yield_non_empty",
    "zipmap",
]
