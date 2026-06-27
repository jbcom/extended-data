"""Package version helpers."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


def get_version() -> str:
    """Return the installed extended-data distribution version."""
    try:
        return version("extended-data")
    except PackageNotFoundError:
        return "0+unknown"


__version__ = get_version()
