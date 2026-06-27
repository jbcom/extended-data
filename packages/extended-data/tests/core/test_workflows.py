"""Integration-style workflow tests that dogfood the public helpers together."""

from __future__ import annotations

import datetime
import json

from pathlib import Path

import pytest

from extended_data import (
    DataFile,
    DataSyncResult,
    DataWorkflow,
    ExtendedDict,
    ExtendedList,
    ExtendedTuple,
    WorkflowResult,
    WorkflowStep,
    base64_decode,
    base64_encode,
    data_transform_action,
    list_data_transform_steps,
    read_data_file,
    sync_file_to_file,
    sync_value_to_file,
    write_file,
)
from extended_data.primitives import decode_hcl2, encode_hcl2
from extended_data.primitives.formats.yaml import YamlTagged


def test_data_workflow_layered_config_round_trip(tmp_path: Path) -> None:
    """DataWorkflow composes Tier 3 file IO with Tier 2 container transforms."""
    base_config = {
        "service": {"name": "api", "debug": False},
        "ports": [8080],
        "features": {"auth": True},
    }
    env_config = {
        "service": {"debug": True},
        "ports": [8081],
        "features": {"metrics": True},
    }

    write_file("config/base.yaml", base_config, tld=tmp_path)
    write_file("config/dev.yaml", env_config, tld=tmp_path)

    env_data = DataWorkflow.from_file("config/dev.yaml", tld=tmp_path).value
    result = (
        DataWorkflow.from_file("config/base.yaml", tld=tmp_path)
        .merge(env_data, name="merge-env")
        .write("build/config.yaml", tld=tmp_path)
    )

    assert isinstance(result, WorkflowResult)
    assert result.output_path == tmp_path / "build" / "config.yaml"
    assert result.steps == ("read:config/base.yaml", "merge-env", "write:build/config.yaml")
    assert result.as_builtin() == {
        "service": {"name": "api", "debug": True},
        "ports": [8080, 8081],
        "features": {"auth": True, "metrics": True},
    }
    assert read_data_file(result.output_path) == result.as_builtin()


def test_data_workflow_runs_named_value_transforms() -> None:
    """DataWorkflow can normalize in-memory API payloads through named steps."""
    raw_payload = {
        "HTTPResponseCode": 200,
        "SelectedServices": ["api", "worker", "db"],
        "Tags": ["api", "api", "docs"],
    }

    def select_services(data: ExtendedDict) -> ExtendedDict:
        return data | {"SelectedServices": data["SelectedServices"].filter_values(denylist=["db"])}

    workflow = DataWorkflow.from_value(raw_payload).run(
        ("select-services", select_services),
        ("deduplicate", lambda data: data.deduplicate()),
        ("unhump", lambda data: data.unhump()),
    )
    result = workflow.result()

    assert workflow.steps == ("value", "select-services", "deduplicate", "unhump")
    assert isinstance(workflow.value, ExtendedDict)
    assert isinstance(workflow.value["selected_services"], ExtendedList)
    assert result.as_builtin() == {
        "http_response_code": 200,
        "selected_services": ["api", "worker"],
        "tags": ["api", "docs"],
    }


def test_data_workflow_deep_merges_mapping_values() -> None:
    """DataWorkflow should expose deep merge without ad hoc lambda steps."""
    workflow = DataWorkflow.from_value({"service": {"name": "api"}, "ports": [8080]}).merge(
        {"service": {"debug": True}, "ports": [8081]},
        name="merge-env",
    )
    result = workflow.result()

    assert workflow.steps == ("value", "merge-env")
    assert isinstance(workflow.value, ExtendedDict)
    assert result.as_builtin() == {
        "service": {"name": "api", "debug": True},
        "ports": [8080, 8081],
    }


def test_data_workflow_merge_file_reads_and_merges_layer(tmp_path: Path) -> None:
    """File-backed merge should use the same decoded DataFile boundary as reads."""
    write_file("base.yaml", {"service": {"name": "api"}, "ports": [8080]}, tld=tmp_path)
    write_file("env.yaml", {"service": {"debug": "true"}, "ports": [8081]}, tld=tmp_path)

    workflow = DataWorkflow.from_file("base.yaml", tld=tmp_path).merge_file("env.yaml", tld=tmp_path)
    result = workflow.transform("reconstruct").result()

    assert workflow.steps == ("read:base.yaml", "merge:env.yaml")
    assert result.steps == ("read:base.yaml", "merge:env.yaml", "transform:reconstruct")
    assert result.as_builtin() == {
        "service": {"name": "api", "debug": True},
        "ports": [8080, 8081],
    }


def test_sync_value_to_file_writes_only_when_rendered_output_changes(tmp_path: Path) -> None:
    """Generic sync should compare the rendered file output before writing."""
    first = sync_value_to_file({"service": "api"}, "config.json", encoding="json", tld=tmp_path)
    second = sync_value_to_file({"service": "api"}, "config.json", encoding="json", tld=tmp_path)

    assert isinstance(first, DataSyncResult)
    assert first.changed is True
    assert first.bytes_written > 0
    assert second.changed is False
    assert second.bytes_written == 0
    assert read_data_file("config.json", tld=tmp_path) == {"service": "api"}


def test_sync_value_to_file_dry_run_reports_change_without_writing(tmp_path: Path) -> None:
    """Dry-run sync should render and compare without mutating the destination."""
    result = sync_value_to_file({"service": "api"}, "config.json", encoding="json", dry_run=True, tld=tmp_path)

    assert result.changed is True
    assert result.dry_run is True
    assert result.bytes_written == 0
    assert not (tmp_path / "config.json").exists()


def test_sync_file_to_file_reads_through_data_file_boundary(tmp_path: Path) -> None:
    """File sync composes DataFile read/decode and sync write behavior."""
    write_file("source.yaml", {"service": {"name": "api"}}, tld=tmp_path)

    result = sync_file_to_file("source.yaml", "dest.json", encoding="json", tld=tmp_path)

    assert result.changed is True
    assert result.source == "source.yaml"
    assert read_data_file("dest.json", tld=tmp_path) == {"service": {"name": "api"}}


def test_data_workflow_sync_file_returns_sync_result(tmp_path: Path) -> None:
    """Workflow sync should expose sync metadata without forcing a WorkflowResult."""
    result = DataWorkflow.from_value({"service": "api"}).sync_file("config.json", encoding="json", tld=tmp_path)

    assert isinstance(result, DataSyncResult)
    assert result.to_dict()["changed"] is True
    assert result.metadata["steps"] == ["value"]


def test_data_workflow_sync_file_preserves_steps_metadata(tmp_path: Path) -> None:
    """Workflow metadata should not overwrite the reserved sync steps key."""
    result = DataWorkflow.from_value({"service": "api"}, metadata={"steps": ["user"], "source": "test"}).sync_file(
        "config.json",
        encoding="json",
        tld=tmp_path,
    )

    assert result.metadata["steps"] == ["value"]
    assert result.metadata["source"] == "test"


def test_data_workflow_merge_requires_mapping_values() -> None:
    """Merge calls should fail loudly when no layer is provided."""
    with pytest.raises(ValueError, match=r"DataWorkflow\.merge requires at least one mapping"):
        DataWorkflow.from_value({"service": "api"}).merge()


def test_data_workflow_merge_reports_shape_mismatch() -> None:
    """Deep merge should fail when the current workflow value is not mapping-shaped."""
    with pytest.raises(TypeError, match="merge is not available for ExtendedList"):
        DataWorkflow.from_value(["api"]).merge({"service": "api"})


def test_data_workflow_applies_shared_named_transforms() -> None:
    """DataWorkflow exposes common Tier 2 transforms without ad hoc lambdas."""
    raw_payload = {
        "HTTPResponseCode": "200",
        "SelectedServices": ["api", "api", "worker"],
        "EmptyValue": "",
    }

    workflow = DataWorkflow.from_value(raw_payload).transform(
        "reconstruct",
        "unhump",
        "deduplicate",
        "compact",
    )
    result = workflow.result()

    assert workflow.steps == (
        "value",
        "transform:reconstruct",
        "transform:unhump",
        "transform:deduplicate",
        "transform:compact",
    )
    assert result.as_builtin() == {
        "http_response_code": 200,
        "selected_services": ["api", "worker"],
    }


def test_data_workflow_reconstruct_transform_handles_scalars() -> None:
    """Named reconstruct should use the scalar string primitive when needed."""
    result = DataWorkflow.from_value("200").transform("reconstruct").result()

    assert result.value == 200


def test_data_transform_action_reports_unknown_steps() -> None:
    """Unknown named transforms should fail at the workflow boundary."""
    with pytest.raises(ValueError, match="unknown data transform 'missing'"):
        data_transform_action("missing")


def test_data_workflow_transform_requires_steps() -> None:
    """Transform calls should not silently preserve the old workflow value."""
    with pytest.raises(ValueError, match=r"DataWorkflow\.transform requires at least one step"):
        DataWorkflow.from_value({"service": "api"}).transform()


def test_data_workflow_transform_reports_shape_mismatch() -> None:
    """Shape-specific named transforms should fail when applied to incompatible data."""
    with pytest.raises(TypeError, match="transform 'unhump' is not available for ExtendedList"):
        DataWorkflow.from_value(["api"]).transform("unhump")


def test_list_data_transform_steps_is_sorted_catalog() -> None:
    """The transform catalog should be deterministic for CLIs and docs."""
    steps = list_data_transform_steps()

    assert steps == tuple(sorted(steps))
    assert {"compact", "reconstruct", "to-snake-case", "unhump"} <= set(steps)


def test_data_workflow_starts_from_data_file_artifact() -> None:
    """DataFile artifacts can start named workflows without manual .data plumbing."""
    artifact = DataFile.decode('{"service": {"name": "api"}}', suffix="json", metadata={"status_code": 200})

    workflow = artifact.workflow().then(("project-name", lambda data: {"name": data["service"]["name"]}))
    result = workflow.result()

    assert workflow.steps == ("data_file:memory", "project-name")
    assert isinstance(workflow.value, ExtendedDict)
    assert workflow.metadata["status_code"] == 200
    assert result.value["name"].upper_first() == "Api"
    assert result.metadata["status_code"] == 200
    assert result.metadata["source"] == "memory"


def test_data_workflow_from_data_file_can_return_builtin_state() -> None:
    """DataFile-to-workflow composition can explicitly lower to plain Python values."""
    artifact = DataFile.decode('{"service": {"name": "api"}}', suffix="json")

    workflow = DataWorkflow.from_data_file(artifact, as_extended=False)

    assert workflow.steps == ("data_file:memory",)
    assert isinstance(workflow.value, dict)
    assert not isinstance(workflow.value, ExtendedDict)
    assert workflow.metadata["encoding"] == "json"


def test_data_workflow_metadata_survives_state_transitions(tmp_path: Path) -> None:
    """Workflow metadata should stay promoted through transforms, lowering, and writes."""
    write_file("config/service.json", {"service": {"name": "api"}}, tld=tmp_path)

    workflow = (
        DataWorkflow.from_file("config/service.json", tld=tmp_path)
        .then(("project", lambda data: {"name": data["service"]["name"]}))
        .as_builtin()
        .as_extended()
    )
    result = workflow.write("build/service.json", tld=tmp_path)

    assert workflow.metadata["source"] == "config/service.json"
    assert workflow.metadata["encoding"] == "json"
    assert workflow.metadata["path"] == str((tmp_path / "config" / "service.json").resolve())
    assert result.metadata == workflow.metadata
    assert result.output_path == tmp_path / "build" / "service.json"


def test_workflow_metadata_views_are_detached() -> None:
    """Workflow and result metadata accessors should not expose mutable internals."""
    workflow = DataWorkflow.from_value({"service": "api"}, metadata={"source": {"name": "payload"}})
    result = workflow.result()

    workflow_metadata = workflow.metadata
    result_metadata = result.metadata
    workflow_metadata["source"]["name"] = "mutated"
    result_metadata["source"]["name"] = "also-mutated"

    assert workflow.metadata["source"]["name"] == "payload"
    assert result.metadata["source"]["name"] == "payload"


def test_data_workflow_preserves_extended_policy_after_file_decode(tmp_path: Path) -> None:
    """Decoded workflows keep promoting plain transform outputs by default."""
    write_file("config/service.json", {"service": {"name": "api"}}, tld=tmp_path)

    result = (
        DataWorkflow.from_file("config/service.json", tld=tmp_path)
        .then(("project", lambda _data: {"name": "api"}))
        .result()
    )

    assert isinstance(result.value, ExtendedDict)
    assert result.value["name"].upper_first() == "Api"


def test_workflow_step_can_be_reused() -> None:
    """WorkflowStep gives reusable transforms first-class names."""
    select_service_name = WorkflowStep("select-service-name", lambda data: data["service"]["name"].upper_first())

    result = DataWorkflow.decode('{"service": {"name": "api"}}', suffix="json").then(select_service_name).result()

    assert result.steps == ("decode:json", "select-service-name")
    assert result.value == "Api"


def test_data_workflow_can_lower_and_promote_values() -> None:
    """Workflow states can move between Tier 2 containers and built-ins explicitly."""
    workflow = DataWorkflow.from_value({"service": {"name": "api"}})
    builtin = workflow.as_builtin()
    extended = builtin.as_extended()

    assert isinstance(workflow.value, ExtendedDict)
    assert isinstance(builtin.value, dict)
    assert not isinstance(builtin.value, ExtendedDict)
    assert isinstance(extended.value, ExtendedDict)
    assert extended.value["service"]["name"].upper_first() == "Api"


def test_workflow_result_extended_view_is_detached() -> None:
    """WorkflowResult accessors expose promoted data without sharing mutable state."""
    result = DataWorkflow.from_value({"service": {"name": "api"}}).result()

    promoted = result.as_extended()
    promoted["service"]["name"] = "worker"

    assert isinstance(promoted, ExtendedDict)
    assert isinstance(result.value, ExtendedDict)
    assert result.value["service"]["name"] == "api"
    assert result.as_extended()["service"]["name"].upper_first() == "Api"


def test_workflow_result_exports_from_completed_value() -> None:
    """Completed workflow results can be exported without leaving the result boundary."""
    result = DataWorkflow.from_value(
        {"launched": datetime.date(2026, 6, 10), "service": {"name": "api"}},
    ).result()

    export_safe = result.to_export_safe()
    wrapped = result.wrap_for_export(allow_encoding="json")

    assert export_safe == {"launched": "2026-06-10", "service": {"name": "api"}}
    assert json.loads(wrapped) == {"launched": "2026-06-10", "service": {"name": "api"}}


def test_data_workflow_preserves_tuples_until_serialization(tmp_path: Path) -> None:
    """Workflow values keep tuple shape in memory and serialize to JSON arrays at the edge."""
    workflow = DataWorkflow.from_value({"aliases": ("api", "gateway")})

    assert isinstance(workflow.value["aliases"], ExtendedTuple)
    assert workflow.result().as_builtin() == {"aliases": ("api", "gateway")}

    result = workflow.write("build/aliases.json", tld=tmp_path)

    assert read_data_file(result.output_path) == {"aliases": ["api", "gateway"]}


def test_data_workflow_missing_file_fails_loudly(tmp_path: Path) -> None:
    """Missing workflow inputs are hard failures, not placeholder results."""
    with pytest.raises(FileNotFoundError):
        DataWorkflow.from_file("config/missing.yaml", tld=tmp_path)


def test_data_workflow_empty_write_fails_loudly(tmp_path: Path) -> None:
    """Empty workflow outputs require an explicit opt-in."""
    with pytest.raises(ValueError, match="Workflow output was empty"):
        DataWorkflow.from_value(None).write("build/empty.json", tld=tmp_path)


def test_layered_config_workflow_round_trip(tmp_path: Path) -> None:
    """Compose file helpers and deep merging through a layered config workflow."""
    base_config = {
        "service": {"name": "api", "debug": False},
        "ports": [8080],
        "features": {"auth": True},
    }
    env_config = {
        "service": {"debug": True},
        "ports": [8081],
        "features": {"metrics": True},
    }

    write_file("config/base.yaml", base_config, tld=tmp_path)
    write_file("config/dev.yaml", env_config, tld=tmp_path)

    base_data = read_data_file("config/base.yaml", tld=tmp_path)
    env_data = read_data_file("config/dev.yaml", tld=tmp_path)
    merged = base_data.deep_merge(env_data)

    output_path = write_file("build/config.yaml", merged, tld=tmp_path)

    assert isinstance(base_data, ExtendedDict)
    assert isinstance(merged, ExtendedDict)
    assert output_path == tmp_path / "build" / "config.yaml"
    assert read_data_file(output_path) == {
        "service": {"name": "api", "debug": True},
        "ports": [8080, 8081],
        "features": {"auth": True, "metrics": True},
    }


def test_terraform_handoff_workflow_round_trip() -> None:
    """Compose HCL and Base64 helpers without dropping down into internals."""
    terraform = {
        "locals": [{"region": "us-east-1"}],
        "resource": [
            {
                "aws_s3_bucket": {
                    "logs": {
                        "bucket": "my-logs-bucket",
                        "acl": "private",
                    }
                }
            }
        ],
    }

    encoded = base64_encode(encode_hcl2(terraform), wrap_raw_data=False)
    decoded = base64_decode(encoded, unwrap_raw_data=False)

    assert decode_hcl2(decoded) == terraform


def test_api_payload_normalization_workflow_round_trip(tmp_path: Path) -> None:
    """Compose list, map, string, and file helpers into a normalized payload flow."""
    payload = ExtendedDict(
        {
            "HTTPResponseCode": 200,
            "SelectedServices": ExtendedList(["api", "worker", "db"]).filter_values(denylist=["db"]),
            "Tags": ["api", "api", "docs"],
        }
    )

    normalized = payload.deduplicate().unhump()

    output_path = write_file("build/payload.json", normalized, tld=tmp_path)

    assert output_path == tmp_path / "build" / "payload.json"
    assert isinstance(normalized, ExtendedDict)
    assert read_data_file(output_path) == {
        "http_response_code": 200,
        "selected_services": ["api", "worker"],
        "tags": ["api", "docs"],
    }


def test_api_payload_factory_workflow_round_trip(tmp_path: Path) -> None:
    """Promote decoded API payloads into containers before normalization."""
    raw_payload = {
        "HTTPResponseCode": 200,
        "SelectedServices": ExtendedList(["api", "worker", "db"]).filter_values(denylist=["db"]),
        "Tags": ["api", "api", "docs"],
    }

    raw_path = write_file("build/raw-payload.json", raw_payload, tld=tmp_path)
    decoded = read_data_file(raw_path)
    normalized = decoded.deduplicate().unhump()

    output_path = write_file("build/payload.json", normalized, tld=tmp_path)

    assert output_path == tmp_path / "build" / "payload.json"
    assert isinstance(decoded, ExtendedDict)
    assert isinstance(normalized, ExtendedDict)
    assert read_data_file(output_path) == {
        "http_response_code": 200,
        "selected_services": ["api", "worker"],
        "tags": ["api", "docs"],
    }


def test_yaml_native_workflow_round_trip(tmp_path: Path) -> None:
    """Preserve YAML-native tagged values through the root write/read/decode surface."""
    template = {
        "bucket_name": YamlTagged("!Ref", "BucketName"),
        "script": "echo one\necho two",
    }

    output_path = write_file("template.yaml", template, tld=tmp_path)
    decoded = read_data_file(output_path)

    assert output_path == tmp_path / "template.yaml"
    assert isinstance(decoded, ExtendedDict)
    assert isinstance(decoded["bucket_name"], YamlTagged)
    assert decoded["bucket_name"].tag == "!Ref"
    assert decoded["bucket_name"].__wrapped__ == "BucketName"
    assert decoded["script"] == "echo one\necho two"
