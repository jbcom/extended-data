"""Integration-style workflow tests that dogfood the public helpers together."""

from __future__ import annotations

import datetime
import json

from pathlib import Path

import pytest

from extended_data import (
    DataWorkflow,
    ExtendedDict,
    ExtendedList,
    ExtendedTuple,
    WorkflowResult,
    WorkflowStep,
    base64_decode,
    base64_encode,
    read_data_file,
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
        .then(("merge-env", lambda data: data.deep_merge(env_data)))
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
