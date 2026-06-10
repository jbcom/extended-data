"""Tests for the integrated extended-data package surface."""

from __future__ import annotations

from importlib.metadata import version

import extended_data
import extended_data.logging as lifecycle_logging

from extended_data import connectors, inputs
from extended_data.connectors.connectors import ConnectorFabric


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
