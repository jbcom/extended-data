"""Pytest fixtures and assertions for Extended Data consumers."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

import pytest


if TYPE_CHECKING:
    from extended_data import ExtendedData


def _extended_data_type() -> type[ExtendedData]:
    from extended_data import ExtendedData

    return ExtendedData


def assert_extended_shape(value: ExtendedData, shape: str) -> None:
    """Assert that an Extended Data value has the expected broad shape."""
    extended_data = _extended_data_type()
    if not isinstance(value, extended_data):
        raise TypeError(f"expected ExtendedData value, got {type(value).__name__}")
    assert value.shape == shape, f"expected ExtendedData shape {shape!r}, got {value.shape!r}"


def assert_builtin_round_trip(value: ExtendedData, expected: Any) -> None:
    """Assert that an Extended Data value lowers to the expected built-in data."""
    extended_data = _extended_data_type()
    if not isinstance(value, extended_data):
        raise TypeError(f"expected ExtendedData value, got {type(value).__name__}")

    actual = value.as_builtin()
    assert actual == expected, f"expected built-in data {expected!r}, got {actual!r}"

    round_trip = extended_data(actual).as_builtin()
    assert round_trip == expected, f"expected round-trip data {expected!r}, got {round_trip!r}"


@pytest.fixture
def extended_data_factory() -> Callable[[Any], ExtendedData]:
    """Return the polymorphic Extended Data constructor."""
    return _extended_data_type()


@pytest.fixture
def extended_data_payload() -> Mapping[str, Any]:
    """Return a representative nested mapping payload."""
    return {
        "service": {
            "name": "api",
            "ports": [8080, 8443],
        },
        "enabled": True,
    }


@pytest.fixture
def extended_data_value(extended_data_payload: Mapping[str, Any]) -> ExtendedData:
    """Return the sample payload promoted to Extended Data."""
    return _extended_data_type()(extended_data_payload)
