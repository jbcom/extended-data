"""Tests for connector optional dependency helpers."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from extended_data.connectors import _optional


def test_get_crewai_tool_decorator_explains_user_managed_install(monkeypatch) -> None:
    """Missing CrewAI reports the deliberate no-extra install policy."""

    def fake_import_module(name: str) -> object:
        if name == "crewai.tools":
            raise ImportError("No module named 'crewai'")
        pytest.fail(f"unexpected import: {name}")

    monkeypatch.setattr(_optional.importlib, "import_module", fake_import_module)

    with pytest.raises(ImportError) as exc_info:
        _optional.get_crewai_tool_decorator()

    message = str(exc_info.value)
    assert "crewai is required for CrewAI tools" in message
    assert "extended-data does not publish a CrewAI extra" in message
    assert "chromadb" in message
    assert "extended-data[crewai]" not in message


def test_get_crewai_tool_decorator_returns_tool_decorator(monkeypatch) -> None:
    """Installed CrewAI tool support is returned directly."""
    sentinel = object()

    monkeypatch.setattr(_optional.importlib, "import_module", lambda name: SimpleNamespace(tool=sentinel))

    assert _optional.get_crewai_tool_decorator() is sentinel


def test_get_crewai_tool_decorator_rejects_incompatible_crewai(monkeypatch) -> None:
    """A CrewAI install without crewai.tools.tool is treated as unsupported."""
    monkeypatch.setattr(_optional.importlib, "import_module", lambda name: SimpleNamespace())

    with pytest.raises(ImportError, match="does not expose it"):
        _optional.get_crewai_tool_decorator()
