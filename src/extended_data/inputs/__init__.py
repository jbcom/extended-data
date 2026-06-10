"""Directed Inputs Class.

This package provides tools for managing and processing directed inputs from
various sources like environment variables, stdin, and predefined dictionaries.
"""

from __future__ import annotations

from extended_data.inputs.__main__ import DirectedInputsClass
from extended_data.inputs.decorators import directed_inputs, input_config


__version__ = "2.1.1"

__all__ = ["DirectedInputsClass", "directed_inputs", "input_config"]
