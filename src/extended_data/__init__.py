"""Extended Data.

This package provides Python utilities for structured data primitives, inputs,
logging, external data connectors, and workflow-oriented integrations.
"""

from __future__ import annotations

import importlib

from typing import TYPE_CHECKING, Any

from extended_data._version import __version__
from extended_data.containers import (
    ExtendedDict,
    ExtendedList,
    ExtendedSet,
    ExtendedString,
    ExtendedTuple,
    extend_data,
    to_builtin,
)
from extended_data.io.base64 import base64_decode, base64_encode
from extended_data.io.exporters import (
    make_raw_data_export_safe,
    wrap_raw_data_for_export,
)
from extended_data.io.files import (
    DataFile,
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
    read_data_file,
    read_file,
    resolve_local_path,
    write_file,
)
from extended_data.io.importers import unwrap_raw_data_from_import
from extended_data.primitives.formats.errors import DataDecodeError
from extended_data.workflows import DataWorkflow, StepLike, WorkflowAction, WorkflowResult, WorkflowStep


if TYPE_CHECKING:
    from extended_data.connectors import (
        AnthropicConnector,
        AWSConnector,
        ConnectorBase,
        ConnectorFabric,
        ConnectorInfo,
        CursorConnector,
        GitHubConnector,
        GoogleConnector,
        JulesConnector,
        MeshyConnector,
        SlackConnector,
        VaultConnector,
        ZoomConnector,
        get_connector,
        get_connector_class,
        get_connector_info,
        list_available_connectors,
        list_connector_capabilities,
        list_connector_categories,
        list_connector_info,
        list_connectors,
        list_connectors_by_capability,
        list_connectors_by_category,
    )
    from extended_data.inputs import InputProvider, directed_inputs, input_config
    from extended_data.logging import ExitRunError, KeyTransform, Logging
    from extended_data.secrets import OutputFormat, SecretsConnector, SyncOperation, SyncOptions, SyncResult


_LAZY_EXPORTS = {
    "AWSConnector": ("extended_data.connectors", "AWSConnector"),
    "AnthropicConnector": ("extended_data.connectors", "AnthropicConnector"),
    "ConnectorFabric": ("extended_data.connectors", "ConnectorFabric"),
    "ConnectorInfo": ("extended_data.connectors", "ConnectorInfo"),
    "CursorConnector": ("extended_data.connectors", "CursorConnector"),
    "ExitRunError": ("extended_data.logging", "ExitRunError"),
    "GitHubConnector": ("extended_data.connectors", "GitHubConnector"),
    "GoogleConnector": ("extended_data.connectors", "GoogleConnector"),
    "InputProvider": ("extended_data.inputs", "InputProvider"),
    "JulesConnector": ("extended_data.connectors", "JulesConnector"),
    "KeyTransform": ("extended_data.logging", "KeyTransform"),
    "Logging": ("extended_data.logging", "Logging"),
    "MeshyConnector": ("extended_data.connectors", "MeshyConnector"),
    "OutputFormat": ("extended_data.secrets", "OutputFormat"),
    "SecretsConnector": ("extended_data.secrets", "SecretsConnector"),
    "SlackConnector": ("extended_data.connectors", "SlackConnector"),
    "SyncOperation": ("extended_data.secrets", "SyncOperation"),
    "SyncOptions": ("extended_data.secrets", "SyncOptions"),
    "SyncResult": ("extended_data.secrets", "SyncResult"),
    "VaultConnector": ("extended_data.connectors", "VaultConnector"),
    "ConnectorBase": ("extended_data.connectors", "ConnectorBase"),
    "ZoomConnector": ("extended_data.connectors", "ZoomConnector"),
    "directed_inputs": ("extended_data.inputs", "directed_inputs"),
    "get_connector": ("extended_data.connectors", "get_connector"),
    "get_connector_class": ("extended_data.connectors", "get_connector_class"),
    "get_connector_info": ("extended_data.connectors", "get_connector_info"),
    "input_config": ("extended_data.inputs", "input_config"),
    "list_available_connectors": ("extended_data.connectors", "list_available_connectors"),
    "list_connector_capabilities": ("extended_data.connectors", "list_connector_capabilities"),
    "list_connector_categories": ("extended_data.connectors", "list_connector_categories"),
    "list_connector_info": ("extended_data.connectors", "list_connector_info"),
    "list_connectors": ("extended_data.connectors", "list_connectors"),
    "list_connectors_by_capability": ("extended_data.connectors", "list_connectors_by_capability"),
    "list_connectors_by_category": ("extended_data.connectors", "list_connectors_by_category"),
}


def __getattr__(name: str) -> Any:
    """Lazily expose integrated adapters and processors at the package root."""
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attr_name = _LAZY_EXPORTS[name]
    value = getattr(importlib.import_module(module_name), attr_name)
    globals()[name] = value
    return value


__all__ = [
    "AWSConnector",
    "AnthropicConnector",
    "ConnectorBase",
    "ConnectorFabric",
    "ConnectorInfo",
    "CursorConnector",
    "DataDecodeError",
    "DataFile",
    "DataWorkflow",
    "ExitRunError",
    "ExtendedDict",
    "ExtendedList",
    "ExtendedSet",
    "ExtendedString",
    "ExtendedTuple",
    "FilePath",
    "GitHubConnector",
    "GoogleConnector",
    "InputProvider",
    "JulesConnector",
    "KeyTransform",
    "Logging",
    "MeshyConnector",
    "OutputFormat",
    "SecretsConnector",
    "SlackConnector",
    "StepLike",
    "SyncOperation",
    "SyncOptions",
    "SyncResult",
    "VaultConnector",
    "WorkflowAction",
    "WorkflowResult",
    "WorkflowStep",
    "ZoomConnector",
    "__version__",
    "base64_decode",
    "base64_encode",
    "clone_repository_to_temp",
    "decode_file",
    "delete_file",
    "directed_inputs",
    "extend_data",
    "file_path_depth",
    "file_path_rel_to_root",
    "get_connector",
    "get_connector_class",
    "get_connector_info",
    "get_encoding_for_file_path",
    "get_parent_repository",
    "get_repository_name",
    "get_tld",
    "input_config",
    "is_url",
    "list_available_connectors",
    "list_connector_capabilities",
    "list_connector_categories",
    "list_connector_info",
    "list_connectors",
    "list_connectors_by_capability",
    "list_connectors_by_category",
    "make_raw_data_export_safe",
    "match_file_extensions",
    "read_data_file",
    "read_file",
    "resolve_local_path",
    "to_builtin",
    "unwrap_raw_data_from_import",
    "wrap_raw_data_for_export",
    "write_file",
]
