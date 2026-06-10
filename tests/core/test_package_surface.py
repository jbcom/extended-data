"""Tests for the integrated extended-data package surface."""

from __future__ import annotations

from importlib.metadata import version

import extended_data
import extended_data.logging as lifecycle_logging

from extended_data import connectors, inputs
from extended_data.connectors.connectors import ConnectorFabric
from extended_data.inputs import InputProvider
from extended_data.logging import Logging


def test_package_version_is_distribution_version() -> None:
    """All integrated package namespaces expose the distribution version."""
    expected = version("extended-data")

    assert extended_data.__version__ == expected
    assert connectors.__version__ == expected
    assert inputs.__version__ == expected
    assert lifecycle_logging.__version__ == expected


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
    assert callable(extended_data.directed_inputs)
    assert callable(extended_data.get_connector)
    assert callable(extended_data.list_connector_info)
