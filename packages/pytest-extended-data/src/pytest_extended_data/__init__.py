"""Pytest helpers for projects using Extended Data."""

from __future__ import annotations

from pytest_extended_data.plugin import assert_builtin_round_trip, assert_extended_shape


__all__ = [
    "assert_builtin_round_trip",
    "assert_extended_shape",
]
