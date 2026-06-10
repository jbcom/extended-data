"""Tests for connector optional dependency helpers."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import tomlkit

from extended_data.connectors import _optional, registry
from extended_data.containers import ExtendedDict, ExtendedList, ExtendedString


REPO_ROOT = Path(__file__).resolve().parents[2]


def _pyproject() -> tomlkit.TOMLDocument:
    return tomlkit.parse((REPO_ROOT / "pyproject.toml").read_text())


def test_builtin_connector_metadata_maps_stay_aligned() -> None:
    """Built-in connector registries should fail fast when metadata drifts."""
    names = set(registry.BUILTIN_CONNECTORS)

    assert names == set(_optional.CONNECTOR_REQUIREMENTS)
    assert names == set(_optional.CONNECTOR_EXTRAS)

    for name, spec in registry.BUILTIN_CONNECTORS.items():
        extra = _optional.get_extra_for_connector(name)
        assert isinstance(extra, ExtendedString)
        assert extra == spec.extra


def test_connector_optional_metadata_returns_extended_values(monkeypatch) -> None:
    """Connector optional dependency metadata helpers return extended values."""
    monkeypatch.setattr(_optional, "is_available", lambda package: package == "present")
    monkeypatch.setitem(_optional.CONNECTOR_REQUIREMENTS, "custom", ["present", "missing"])
    monkeypatch.setitem(_optional.CONNECTOR_EXTRAS, "custom", "custom-extra")

    package_extra = _optional.get_extra_for_package("boto3")
    connector_extra = _optional.get_extra_for_connector("custom")
    requirements = _optional.get_connector_requirements("custom")
    missing = _optional.get_missing_connector_requirements("custom")
    install = _optional.get_connector_install_command("custom")

    assert isinstance(package_extra, ExtendedString)
    assert package_extra == "aws"
    assert isinstance(connector_extra, ExtendedString)
    assert connector_extra == "custom-extra"
    assert isinstance(requirements, ExtendedList)
    assert requirements == ["present", "missing"]
    assert isinstance(requirements[0], ExtendedString)
    assert isinstance(missing, ExtendedList)
    assert missing == ["missing"]
    assert isinstance(missing[0], ExtendedString)
    assert isinstance(install, ExtendedString)
    assert install == "pip install extended-data[custom-extra]"


def test_builtin_connectors_are_registered_as_entry_points() -> None:
    """Every built-in connector should be published through the connector entry point group."""
    entry_points = _pyproject()["project"]["entry-points"]["extended_data.connectors"]

    assert set(entry_points) == set(registry.BUILTIN_CONNECTORS)

    for name, spec in registry.BUILTIN_CONNECTORS.items():
        assert entry_points[name] == f"{spec.module_path}:{spec.class_name}"


def test_connector_extras_exist_in_pyproject() -> None:
    """Connector extras referenced by registry metadata should exist in pyproject."""
    extras = _pyproject()["project"]["optional-dependencies"]

    for name, extra in _optional.CONNECTOR_EXTRAS.items():
        assert extra in extras, f"{name} uses missing extra {extra}"


def test_connector_requirement_packages_map_to_connector_extras() -> None:
    """Connector import checks should point users to the same extra as the connector itself."""
    for name, requirements in _optional.CONNECTOR_REQUIREMENTS.items():
        extra = _optional.CONNECTOR_EXTRAS[name]

        for requirement in requirements:
            assert _optional.PACKAGE_TO_EXTRA[requirement] == extra


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


def test_framework_detection_returns_extended_metadata(monkeypatch) -> None:
    """AI framework availability helpers return first-class extended values."""
    available = {"langchain_core": True, "crewai": False, "strands": True, "mcp": False}
    monkeypatch.setattr(_optional, "is_available", lambda package: available[package])

    detected = _optional.detect_ai_frameworks()
    frameworks = _optional.get_available_ai_frameworks()

    assert isinstance(detected, ExtendedDict)
    assert detected == {"langchain": True, "crewai": False, "strands": True, "mcp": False}
    assert isinstance(frameworks, ExtendedList)
    assert frameworks == ["langchain", "strands"]
    assert isinstance(frameworks[0], ExtendedString)


def test_available_connectors_returns_extended_names(monkeypatch) -> None:
    """Connector availability helper returns first-class extended names."""
    monkeypatch.setattr(_optional, "is_connector_available", lambda connector: connector in {"cursor", "meshy"})

    connectors = _optional.get_available_connectors()

    assert isinstance(connectors, ExtendedList)
    assert "cursor" in connectors
    assert "meshy" in connectors
    assert isinstance(connectors[0], ExtendedString)
