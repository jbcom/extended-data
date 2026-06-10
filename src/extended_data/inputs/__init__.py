"""Input loading and decoding primitives.

This package provides tools for managing and processing directed inputs from
various sources like environment variables, stdin, and predefined dictionaries.
"""

from __future__ import annotations

from extended_data._version import __version__
from extended_data.inputs.__main__ import InputProvider
from extended_data.inputs.decorators import directed_inputs, input_config


__all__ = ["InputProvider", "__version__", "directed_inputs", "input_config"]
