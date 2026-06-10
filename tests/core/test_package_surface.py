"""Tests for the integrated extended-data package surface."""

from __future__ import annotations

from importlib import util
from importlib.metadata import version
from types import ModuleType
from typing import get_type_hints

import extended_data
import extended_data.logging as lifecycle_logging

from extended_data import connectors, containers, inputs, io, primitives, secrets, workflows
from extended_data.connectors.connectors import ConnectorFabric
from extended_data.connectors.registry import BUILTIN_CONNECTORS
from extended_data.containers import ExtendedDict, ExtendedList, ExtendedString, ExtendedTuple
from extended_data.inputs import InputProvider
from extended_data.logging import Logging


PUBLIC_MODULES = (
    extended_data,
    primitives,
    containers,
    io,
    inputs,
    lifecycle_logging,
    connectors,
    secrets,
    workflows,
)


def _assert_public_exports_resolve(module: ModuleType) -> None:
    exports = module.__all__

    assert len(exports) == len(set(exports)), f"{module.__name__}.__all__ contains duplicates"

    for name in exports:
        value = getattr(module, name)

        assert value is not None, f"{module.__name__}.{name} exported None"


def test_package_version_is_distribution_version() -> None:
    """All integrated package namespaces expose the distribution version."""
    expected = version("extended-data")

    assert extended_data.__version__ == expected
    assert connectors.__version__ == expected
    assert inputs.__version__ == expected
    assert lifecycle_logging.__version__ == expected
    assert secrets.__version__ == expected


def test_public_all_exports_resolve_to_real_values() -> None:
    """Public package modules should not advertise missing or sentinel exports."""
    for module in PUBLIC_MODULES:
        _assert_public_exports_resolve(module)


def test_public_all_exports_are_import_star_visible() -> None:
    """Star imports should expose exactly the advertised public names."""
    for module in PUBLIC_MODULES:
        namespace: dict[str, object] = {}
        exec(f"from {module.__name__} import *", {}, namespace)
        namespace.pop("__builtins__", None)

        assert set(namespace) == set(module.__all__)


def test_root_exports_tiered_data_surfaces() -> None:
    """The root package should expose the integrated primitive, container, IO, and workflow surfaces."""
    for module in (primitives, containers, io, workflows):
        assert set(module.__all__) <= set(extended_data.__all__), module.__name__


def test_clean_major_version_public_names() -> None:
    """The public surface uses integrated extended-data names."""
    assert inputs.InputProvider.__name__ == "InputProvider"
    assert connectors.ConnectorFabric is ConnectorFabric
    assert not hasattr(inputs, "DirectedInputsClass")
    assert not hasattr(connectors, "VendorConnectors")
    assert not hasattr(connectors, "AWSConnectorFull")
    assert not hasattr(connectors, "GoogleConnectorFull")
    assert not hasattr(connectors, "GoogleCloudConnector")
    assert not hasattr(connectors, "GoogleWorkspaceConnector")
    assert not hasattr(connectors, "GoogleBillingConnector")
    assert not hasattr(extended_data, "GoogleCloudConnector")
    assert not hasattr(extended_data, "GoogleWorkspaceConnector")
    assert not hasattr(extended_data, "GoogleBillingConnector")
    assert not hasattr(primitives, "SortedDefaultDict")
    assert not hasattr(extended_data, "SortedDefaultDict")
    assert not hasattr(primitives, "removeprefix")
    assert not hasattr(primitives, "removesuffix")
    assert not hasattr(primitives, "bytestostr")
    assert not hasattr(extended_data, "removeprefix")
    assert not hasattr(extended_data, "removesuffix")
    assert not hasattr(extended_data, "bytestostr")
    old_type_converters = (
        "strtobool",
        "strtodate",
        "strtodatetime",
        "strtofloat",
        "strtoint",
        "strtopath",
        "strtotime",
    )
    for old_name in old_type_converters:
        assert not hasattr(primitives, old_name)
        assert not hasattr(extended_data, old_name)


def test_old_monorepo_import_namespaces_are_not_preserved() -> None:
    """Old package import namespaces should remain absent in the clean major version."""
    old_namespaces = (
        "directed_inputs_class",
        "extended_data_types",
        "lifecyclelogging",
        "vendor_connectors",
    )

    for namespace in old_namespaces:
        assert util.find_spec(namespace) is None


def test_root_exports_first_class_integrated_primitives() -> None:
    """Inputs, logging, and connector fabric are available from the root package."""
    assert extended_data.DataDecodeError.__name__ == "DataDecodeError"
    assert extended_data.DataWorkflow.__name__ == "DataWorkflow"
    assert extended_data.InputProvider is InputProvider
    assert extended_data.Logging is Logging
    assert extended_data.ConnectorFabric is ConnectorFabric
    assert extended_data.ConnectorInfo.__name__ == "ConnectorInfo"
    assert extended_data.WorkflowResult.__name__ == "WorkflowResult"
    assert extended_data.WorkflowStep.__name__ == "WorkflowStep"
    assert extended_data.SecretsConnector is secrets.SecretsConnector
    assert extended_data.SyncOptions is secrets.SyncOptions
    assert extended_data.SyncResult is secrets.SyncResult
    assert extended_data.SyncOperation is secrets.SyncOperation
    assert extended_data.OutputFormat is secrets.OutputFormat
    assert callable(extended_data.directed_inputs)
    assert extended_data.number_to_words(42) == "forty-two"
    assert extended_data.to_roman(42) == "XLII"
    assert extended_data.normalize_data_encoding("YML") == "yaml"
    assert callable(extended_data.read_data_file)
    assert callable(extended_data.get_connector)
    assert callable(extended_data.list_connector_info)
    connector_names = extended_data.list_connectors()
    assert isinstance(connector_names, ExtendedList)
    assert isinstance(connector_names[0], ExtendedString)
    assert get_type_hints(connectors.list_connectors)["return"] == ExtendedList[ExtendedString]
    assert get_type_hints(ConnectorFabric.list_connectors)["return"] == ExtendedList[ExtendedString]
    assert "github" in connector_names


def test_tier2_container_methods_expose_integrated_primitives() -> None:
    """Tier 2 containers should expose common primitive operations directly."""
    matched = ExtendedString("api-gateway").is_partial_match("gateway")
    typed = ExtendedList(["api", 2]).split_by_type(primitive_only=True)
    mapped = ExtendedTuple(("service", "region")).zipmap(("api", "us-east-1"))
    first_entry = ExtendedDict({"empty": "", "service": "api"}).first_non_empty_entry("empty", "service")
    selected = ExtendedList([None, "", {"service": "api"}]).first_non_empty()

    assert matched is True
    assert isinstance(typed, ExtendedDict)
    assert typed["str"] == ["api"]
    assert isinstance(mapped, ExtendedDict)
    assert mapped["service"].upper_first() == "Api"
    assert isinstance(first_entry, ExtendedDict)
    assert first_entry["service"].upper_first() == "Api"
    assert isinstance(selected, ExtendedDict)
    assert selected["service"].upper_first() == "Api"


def test_connectors_root_exports_builtin_connector_classes() -> None:
    """Every built-in registry connector class is exported from the connector package root."""
    for spec in BUILTIN_CONNECTORS.values():
        value = getattr(connectors, spec.class_name)

        assert isinstance(value, type)
        assert value.__name__ == spec.class_name


def test_package_root_exports_builtin_connector_classes() -> None:
    """Built-in connector classes are first-class root package exports."""
    for spec in BUILTIN_CONNECTORS.values():
        root_value = getattr(extended_data, spec.class_name)
        connector_value = getattr(connectors, spec.class_name)

        assert root_value is connector_value


def test_first_class_connectors_keep_operation_mixins_without_optional_extras() -> None:
    """Unified connector classes should expose real operation mixins before SDK extras are installed."""
    assert callable(connectors.AWSConnector.list_s3_buckets)
    assert callable(connectors.AWSConnector.get_organization_accounts)
    assert callable(connectors.AWSConnector.list_sso_users)
    assert callable(connectors.GoogleConnector.list_projects)
    assert callable(connectors.GoogleConnector.list_users)
    assert callable(connectors.GoogleConnector.list_billing_accounts)


def test_google_registry_uses_single_first_class_connector() -> None:
    """Google Workspace, Cloud, and Billing operations should not be split into connector aliases."""
    connector_names = set(connectors.list_connectors())

    assert "google" in connector_names
    assert "google_cloud" not in connector_names
    assert "google_workspace" not in connector_names
    assert "google_billing" not in connector_names


def test_clean_major_version_does_not_preserve_duplicate_tool_modules() -> None:
    """Secrets tool factories live on the package root and connector implementation module."""
    assert util.find_spec("extended_data.secrets.tools") is None
    assert callable(secrets.get_tools)
    assert callable(secrets.get_langchain_tools)
    assert callable(secrets.get_crewai_tools)
    assert callable(secrets.get_strands_tools)
    assert callable(connectors.SecretsConnector)
