from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

import pytest

from extended_data import ExtendedData, ExtendedDict
from pytest_extended_data import assert_builtin_round_trip, assert_extended_shape, plugin


def test_extended_data_factory_fixture_promotes_payload(
    extended_data_factory: Callable[[Any], ExtendedData],
    extended_data_payload: Mapping[str, Any],
) -> None:
    value = extended_data_factory(extended_data_payload)

    assert isinstance(value, ExtendedDict)
    assert_extended_shape(value, "mapping")
    assert_builtin_round_trip(value, dict(extended_data_payload))


def test_extended_data_value_fixture_is_ready_to_assert(extended_data_value: ExtendedData) -> None:
    assert_extended_shape(extended_data_value, "mapping")
    assert extended_data_value["service"]["name"] == "api"


def test_assert_extended_shape_rejects_non_extended_values() -> None:
    with pytest.raises(TypeError, match="expected ExtendedData value"):
        assert_extended_shape("api", "scalar")


def test_assert_extended_shape_rejects_wrong_shape() -> None:
    with pytest.raises(AssertionError, match="expected ExtendedData shape 'sequence'"):
        assert_extended_shape(ExtendedData({"service": "api"}), "sequence")


def test_assert_builtin_round_trip_rejects_non_extended_values() -> None:
    with pytest.raises(TypeError, match="expected ExtendedData value"):
        assert_builtin_round_trip({"service": "api"}, {"service": "api"})


def test_assert_builtin_round_trip_rejects_wrong_builtin_value() -> None:
    with pytest.raises(AssertionError, match="expected built-in data"):
        assert_builtin_round_trip(ExtendedData({"service": "api"}), {"service": "worker"})


def test_assert_builtin_round_trip_rejects_unstable_round_trip(monkeypatch: pytest.MonkeyPatch) -> None:
    class UnstableExtendedData:
        shape = "mapping"

        def __init__(self, value: Any, *, stable: bool = False) -> None:
            self.value = value
            self.stable = stable

        def as_builtin(self) -> Any:
            if self.stable:
                return self.value
            return {"changed": self.value}

    monkeypatch.setattr(plugin, "_extended_data_type", lambda: UnstableExtendedData)

    with pytest.raises(AssertionError, match="expected round-trip data"):
        plugin.assert_builtin_round_trip(UnstableExtendedData({"service": "api"}, stable=True), {"service": "api"})
