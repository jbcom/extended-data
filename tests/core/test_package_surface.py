"""Tests for the integrated extended-data package surface."""

from __future__ import annotations

from importlib import util
from importlib.metadata import version
from types import ModuleType

import extended_data
import extended_data.logging as lifecycle_logging

from extended_data import connectors, containers, inputs, io, primitives, secrets, workflows
from extended_data.connectors.connectors import ConnectorFabric
from extended_data.connectors.registry import BUILTIN_CONNECTORS
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
    assert callable(extended_data.get_connector)
    assert callable(extended_data.list_connector_info)


def test_connectors_root_exports_builtin_connector_classes() -> None:
    """Every built-in registry connector class is exported from the connector package root."""
    for spec in BUILTIN_CONNECTORS.values():
        value = getattr(connectors, spec.class_name)

        assert isinstance(value, type)
        assert value.__name__ == spec.class_name


def test_aws_full_connector_keeps_operation_mixins_without_aws_extra() -> None:
    """AWSConnectorFull should expose real operation mixins even before boto3 is installed."""
    assert callable(connectors.AWSConnectorFull.list_s3_buckets)
    assert callable(connectors.AWSConnectorFull.get_organization_accounts)
    assert callable(connectors.AWSConnectorFull.list_sso_users)


def test_clean_major_version_does_not_preserve_duplicate_tool_modules() -> None:
    """Secrets tool factories live on the package root and connector implementation module."""
    assert util.find_spec("extended_data.secrets.tools") is None
    assert callable(secrets.get_tools)
    assert callable(connectors.SecretsConnector)
