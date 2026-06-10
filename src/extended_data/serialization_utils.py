"""Internal helpers for supported serialization format handling."""

from __future__ import annotations

from typing import overload


_ENCODING_ALIASES: dict[str, str] = {
    "yaml": "yaml",
    "yml": "yaml",
    "json": "json",
    "toml": "toml",
    "tml": "toml",
    "hcl": "hcl",
    "tf": "hcl",
    "tfvars": "hcl",
    "raw": "raw",
    "txt": "raw",
    "text": "raw",
}


@overload
def normalize_data_encoding(encoding: None) -> None: ...


@overload
def normalize_data_encoding(encoding: str) -> str: ...


def normalize_data_encoding(encoding: str | None) -> str | None:
    """Normalize a supported encoding alias to its canonical representation."""
    if encoding is None:
        return None

    encoding_lower = encoding.casefold()
    return _ENCODING_ALIASES.get(encoding_lower, encoding_lower)
