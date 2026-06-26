"""Internal helpers for normalizing data before format encoding."""

from __future__ import annotations

from typing import Any


def lower_extended_data(value: Any) -> Any:
    """Lower Tier 2 containers to plain values before handing data to codecs."""
    from extended_data.containers.factory import to_builtin

    return to_builtin(value)


__all__ = ["lower_extended_data"]
