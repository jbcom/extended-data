"""Tests for the public extended-data package surface."""

from __future__ import annotations

from importlib import util
from importlib.metadata import version
from types import ModuleType

import extended_data
import extended_data.logging as lifecycle_logging

from extended_data import containers, inputs, io, primitives, workflows
from extended_data.containers import (
    ExtendedData,
    ExtendedDict,
    ExtendedList,
    ExtendedSet,
    ExtendedString,
    ExtendedTuple,
)
from extended_data.inputs import InputProvider
from extended_data.logging import Logging


PUBLIC_MODULES = (
    extended_data,
    primitives,
    containers,
    io,
    inputs,
    lifecycle_logging,
    workflows,
)


def _assert_public_exports_resolve(module: ModuleType) -> None:
    exports = module.__all__

    assert len(exports) == len(set(exports)), f"{module.__name__}.__all__ contains duplicates"

    for name in exports:
        value = getattr(module, name)

        assert value is not None, f"{module.__name__}.{name} exported None"


def test_package_version_is_distribution_version() -> None:
    """All integrated package namespaces expose the distribution version."""
    expected = version("extended-data")

    assert extended_data.__version__ == expected
    assert inputs.__version__ == expected
    assert lifecycle_logging.__version__ == expected


def test_public_all_exports_resolve_to_real_values() -> None:
    """Public package modules should not advertise missing or sentinel exports."""
    for module in PUBLIC_MODULES:
        _assert_public_exports_resolve(module)


def test_public_all_exports_are_import_star_visible() -> None:
    """Star imports should expose exactly the advertised public names."""
    for module in PUBLIC_MODULES:
        namespace: dict[str, object] = {}
        exec(f"from {module.__name__} import *", {}, namespace)
        namespace.pop("__builtins__", None)

        assert set(namespace) == set(module.__all__)


def test_root_exports_tiered_data_surfaces() -> None:
    """The root package should expose integrated container, IO, and workflow surfaces."""
    for module in (containers, io, workflows):
        assert set(module.__all__) <= set(extended_data.__all__), module.__name__


def test_tier1_primitives_are_not_root_exports() -> None:
    """Tier 1 functions and codecs should be imported from extended_data.primitives."""
    for name in primitives.__all__:
        assert hasattr(primitives, name), name
        assert not hasattr(extended_data, name), name
        assert name not in extended_data.__all__


def test_clean_major_version_public_names() -> None:
    """The public surface uses integrated extended-data names only."""
    assert inputs.InputProvider.__name__ == "InputProvider"
    assert not hasattr(inputs, "DirectedInputsClass")
    assert not hasattr(primitives, "SortedDefaultDict")
    assert not hasattr(extended_data, "SortedDefaultDict")
    assert not hasattr(primitives, "removeprefix")
    assert not hasattr(primitives, "removesuffix")
    assert not hasattr(primitives, "bytestostr")
    assert not hasattr(extended_data, "removeprefix")
    assert not hasattr(extended_data, "removesuffix")
    assert not hasattr(extended_data, "bytestostr")
    old_type_converters = (
        "strtobool",
        "strtodate",
        "strtodatetime",
        "strtofloat",
        "strtoint",
        "strtopath",
        "strtotime",
    )
    for old_name in old_type_converters:
        assert not hasattr(primitives, old_name)
        assert not hasattr(extended_data, old_name)


def test_old_import_namespaces_are_not_preserved_inside_extended_data() -> None:
    """Clean major-version breaks should not keep old in-package shims."""
    for namespace in (
        "extended_data.connectors",
        "extended_data.secrets",
    ):
        assert util.find_spec(namespace) is None


def test_root_exports_first_class_base_surfaces() -> None:
    """Inputs, logging, IO, containers, and workflows are available from the root package."""
    assert extended_data.DataDecodeError.__name__ == "DataDecodeError"
    assert extended_data.DataFile.__name__ == "DataFile"
    assert extended_data.DataWorkflow.__name__ == "DataWorkflow"
    assert extended_data.ExtendedData.__name__ == "ExtendedData"
    assert extended_data.InputProvider is InputProvider
    assert extended_data.Logging is Logging
    assert extended_data.WorkflowResult.__name__ == "WorkflowResult"
    assert extended_data.WorkflowStep.__name__ == "WorkflowStep"
    assert callable(extended_data.data_transform_action)
    assert callable(extended_data.list_data_transform_steps)
    assert callable(extended_data.directed_inputs)
    assert callable(extended_data.read_data_file)
    assert "unhump" in extended_data.DATA_TRANSFORM_STEPS
    assert "reconstruct" in extended_data.list_data_transform_steps()


def test_logging_exposes_stored_messages_as_detached_tier2_data() -> None:
    """Stored log message collections should be consumable through Tier 2 containers."""
    logger = Logging(enable_console=False, enable_file=False)

    logger.logged_statement("Stored message", storage_marker="events", log_level="info")
    messages = logger.get_stored_messages("events")
    snapshot = logger.snapshot_stored_messages()

    messages.add("Local mutation")

    assert isinstance(messages, ExtendedSet)
    assert isinstance(snapshot, ExtendedDict)
    assert isinstance(snapshot["events"], ExtendedSet)
    assert "Local mutation" not in logger.stored_messages["events"]
    assert sorted(snapshot.to_export_safe()["events"]) == ["Stored message"]


def test_workflow_result_exposes_detached_export_boundaries() -> None:
    """Workflow results should expose promoted and export-safe value boundaries."""
    result = extended_data.DataWorkflow.from_value({"service": {"name": "api"}}).result()

    promoted = result.as_extended()
    promoted["service"]["name"] = "worker"

    assert isinstance(promoted, ExtendedDict)
    assert result.value["service"]["name"] == "api"
    assert result.as_extended()["service"]["name"].upper_first() == "Api"
    assert result.to_export_safe() == {"service": {"name": "api"}}
    assert '"service"' in result.wrap_for_export(allow_encoding="json")


def test_tier2_container_methods_expose_integrated_primitives() -> None:
    """Tier 2 containers should expose common primitive operations directly."""
    matched = ExtendedString("api-gateway").is_partial_match("gateway")
    parsed_int = ExtendedString("42").to_int()
    decoded_string = ExtendedString('{"service": "api"}').decode_json()
    typed = ExtendedList(["api", 2]).split_by_type(primitive_only=True)
    mapped = ExtendedTuple(("service", "region")).zipmap(("api", "us-east-1"))
    first_entry = ExtendedDict({"empty": "", "service": "api"}).first_non_empty_entry("empty", "service")
    selected = ExtendedList([None, "", {"service": "api"}]).first_non_empty()
    reconstructed = ExtendedDict({"enabled": "true", "retries": "5"}).reconstruct_special_types()
    export_safe = ExtendedDict({"launched": "2026-06-10"}).reconstruct_special_types().to_export_safe()

    assert matched is True
    assert parsed_int == 42
    assert isinstance(decoded_string, ExtendedDict)
    assert decoded_string["service"].upper_first() == "Api"
    assert isinstance(typed, ExtendedDict)
    assert typed["str"] == ["api"]
    assert isinstance(mapped, ExtendedDict)
    assert mapped["service"].upper_first() == "Api"
    assert isinstance(first_entry, ExtendedDict)
    assert first_entry["service"].upper_first() == "Api"
    assert isinstance(selected, ExtendedDict)
    assert selected["service"].upper_first() == "Api"
    assert isinstance(reconstructed, ExtendedDict)
    assert reconstructed == {"enabled": True, "retries": 5}
    assert export_safe == {"launched": "2026-06-10"}


def test_redaction_is_a_tier1_primitive() -> None:
    """Diagnostic redaction should live with reusable Tier 1 utilities."""
    assert primitives.redact_sensitive_text("password=hunter2") == "password=[REDACTED]"
    assert primitives.redact_sensitive_data({"api_key": "key_123"}) == {"api_key": "[REDACTED]"}


def test_extended_data_wraps_any_promoted_shape() -> None:
    """ExtendedData should be the generic facade over shape-specific containers."""
    wrapped_dict = ExtendedData({"service": {"name": "api"}, "ports": [8080]})
    wrapped_list = ExtendedData(["api", "api", "worker"])
    wrapped_string = ExtendedData("api-gateway")

    merged = wrapped_dict.merge({"service": {"debug": True}, "ports": [8081]})
    transformed = wrapped_list.unique()

    assert wrapped_dict.data_type == "ExtendedDict"
    assert merged.as_builtin() == {
        "service": {"name": "api", "debug": True},
        "ports": [8080, 8081],
    }
    assert transformed == ["api", "worker"]
    assert wrapped_string.upper_first() == "Api-gateway"
    assert ExtendedData(merged).as_builtin() == merged.as_builtin()


def test_extended_data_truthiness_mirrors_wrapped_value() -> None:
    """ExtendedData should not make scalar falsey values truthy."""
    assert bool(ExtendedData(None)) is False
    assert bool(ExtendedData(False)) is False
    assert bool(ExtendedData(0)) is False
    assert bool(ExtendedData("")) is False
    assert bool(ExtendedData([])) is False
    assert bool(ExtendedData("api")) is True
