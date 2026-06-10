"""Shared framework selection tests for connector tool modules."""

from __future__ import annotations

import importlib

import pytest


TOOL_MODULES = (
    "extended_data.connectors.anthropic.tools",
    "extended_data.connectors.aws.tools",
    "extended_data.connectors.cursor.tools",
    "extended_data.connectors.github.tools",
    "extended_data.connectors.google.tools",
    "extended_data.connectors.meshy.tools",
    "extended_data.connectors.secrets.tools",
    "extended_data.connectors.slack.tools",
    "extended_data.connectors.vault.tools",
    "extended_data.connectors.zoom.tools",
)


@pytest.mark.parametrize("module_path", TOOL_MODULES)
def test_get_tools_rejects_functions_alias(module_path: str) -> None:
    """Plain-function tools should use the canonical strands framework name."""
    module = importlib.import_module(module_path)

    with pytest.raises(ValueError, match="Unknown framework"):
        module.get_tools("functions")
