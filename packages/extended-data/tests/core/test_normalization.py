"""Tests for the internal data normalization helper."""

from __future__ import annotations

from extended_data.containers import ExtendedDict, ExtendedList, ExtendedSet, ExtendedString, ExtendedTuple
from extended_data.primitives.formats._normalization import lower_extended_data


def test_lower_extended_data_unwraps_containers() -> None:
    """lower_extended_data should lower Tier 2 containers to plain Python values."""
    value = ExtendedDict(
        {
            "service": ExtendedString("api"),
            "ports": ExtendedList([80, 443]),
            "tags": ExtendedSet({"prod", "api"}),
            "aliases": ExtendedTuple(("api", "gateway")),
        }
    )

    lowered = lower_extended_data(value)

    assert lowered == {
        "service": "api",
        "ports": [80, 443],
        "tags": {"prod", "api"},
        "aliases": ("api", "gateway"),
    }
    assert type(lowered) is dict
    assert type(lowered["ports"]) is list
    assert type(lowered["tags"]) is set
    assert type(lowered["aliases"]) is tuple


def test_lower_extended_data_passes_through_plain_values() -> None:
    """lower_extended_data should leave plain Python values untouched."""
    assert lower_extended_data(None) is None
    assert lower_extended_data(42) == 42
    assert lower_extended_data("api") == "api"
    assert lower_extended_data({"service": "api"}) == {"service": "api"}


def test_lower_extended_data_unwraps_nested_extended_containers() -> None:
    """lower_extended_data should recursively lower nested Tier 2 containers."""
    value = ExtendedDict({"outer": ExtendedDict({"inner": ExtendedList([ExtendedString("api")])})})

    lowered = lower_extended_data(value)

    assert lowered == {"outer": {"inner": ["api"]}}
    assert type(lowered["outer"]) is dict
    assert type(lowered["outer"]["inner"]) is list
