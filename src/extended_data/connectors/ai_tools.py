"""AI tool definition helpers for Vercel AI SDK compatibility.

This module provides Pydantic-based helpers to define AI tool schemas
that are compatible with the Vercel AI SDK and other modern AI frameworks.
"""

from __future__ import annotations

import builtins

from typing import cast

from pydantic import BaseModel

from extended_data.containers import ExtendedDict, extend_data


def get_pydantic_schema(model: builtins.type[BaseModel]) -> ExtendedDict:
    """Generate a Vercel AI SDK-compatible JSON schema from a Pydantic model.

    This function removes the top-level 'title' and 'description' fields,
    which are often redundant and not used by AI frameworks. Parameter-level
    'description' fields are preserved as they are crucial for the AI to
    understand the tool's inputs.

    Args:
        model: The Pydantic model class.

    Returns:
        An extended JSON schema dictionary.
    """
    schema = model.model_json_schema()

    # Remove top-level title and description
    schema.pop("title", None)
    schema.pop("description", None)

    return cast(ExtendedDict, extend_data(schema))
