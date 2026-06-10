"""Integration-style workflow tests that dogfood the public helpers together."""

from __future__ import annotations

from pathlib import Path

from extended_data import (
    ExtendedDict,
    base64_decode,
    base64_encode,
    decode_file,
    decode_hcl2,
    encode_hcl2,
    filter_list,
    read_file,
    write_file,
)
from extended_data.primitives.formats.yaml import YamlTagged


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

    base_data = decode_file(read_file("config/base.yaml", tld=tmp_path), file_path="config/base.yaml", as_extended=True)
    env_data = decode_file(read_file("config/dev.yaml", tld=tmp_path), file_path="config/dev.yaml", as_extended=True)
    merged = base_data.deep_merge(env_data)

    output_path = write_file("build/config.yaml", merged, tld=tmp_path)

    assert isinstance(base_data, ExtendedDict)
    assert isinstance(merged, ExtendedDict)
    assert output_path == tmp_path / "build" / "config.yaml"
    assert decode_file(read_file(output_path), file_path=output_path) == {
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
            "SelectedServices": filter_list(["api", "worker", "db"], denylist=["db"]),
            "Tags": ["api", "api", "docs"],
        }
    )

    normalized = payload.deduplicate().unhump()

    output_path = write_file("build/payload.json", normalized, tld=tmp_path)

    assert output_path == tmp_path / "build" / "payload.json"
    assert isinstance(normalized, ExtendedDict)
    assert decode_file(read_file(output_path), file_path=output_path) == {
        "http_response_code": 200,
        "selected_services": ["api", "worker"],
        "tags": ["api", "docs"],
    }


def test_api_payload_factory_workflow_round_trip(tmp_path: Path) -> None:
    """Promote decoded API payloads into containers before normalization."""
    raw_payload = {
        "HTTPResponseCode": 200,
        "SelectedServices": filter_list(["api", "worker", "db"], denylist=["db"]),
        "Tags": ["api", "api", "docs"],
    }

    raw_path = write_file("build/raw-payload.json", raw_payload, tld=tmp_path)
    decoded = decode_file(read_file(raw_path), file_path=raw_path, as_extended=True)
    normalized = decoded.deduplicate().unhump()

    output_path = write_file("build/payload.json", normalized, tld=tmp_path)

    assert output_path == tmp_path / "build" / "payload.json"
    assert isinstance(decoded, ExtendedDict)
    assert isinstance(normalized, ExtendedDict)
    assert decode_file(read_file(output_path), file_path=output_path) == {
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
    decoded = decode_file(read_file(output_path), file_path=output_path, as_extended=True)

    assert output_path == tmp_path / "template.yaml"
    assert isinstance(decoded, ExtendedDict)
    assert isinstance(decoded["bucket_name"], YamlTagged)
    assert decoded["bucket_name"].tag == "!Ref"
    assert decoded["bucket_name"].__wrapped__ == "BucketName"
    assert decoded["script"] == "echo one\necho two"
