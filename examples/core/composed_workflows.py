#!/usr/bin/env python3
"""End-to-end workflow examples for Extended Data core.

This script demonstrates how package primitives, containers, and processors
compose into complete configuration and payload pipelines.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from extended_data import (
    DataWorkflow,
    ExtendedList,
    base64_decode,
    base64_encode,
    list_data_transform_steps,
    read_data_file,
    read_file,
    write_file,
)
from extended_data.primitives import decode_hcl2, encode_hcl2
from extended_data.primitives.formats.yaml import YamlTagged


def demonstrate_layered_config_workflow() -> None:
    """Read, decode, merge, and write structured configuration."""
    print("=== Layered Config Workflow ===\n")

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

    with TemporaryDirectory() as tmpdir:
        tld = Path(tmpdir)
        write_file("config/base.yaml", base_config, tld=tld)
        write_file("config/dev.yaml", env_config, tld=tld)

        env_data = DataWorkflow.from_file("config/dev.yaml", tld=tld).value
        result = (
            DataWorkflow.from_file("config/base.yaml", tld=tld)
            .merge(env_data, name="merge-env")
            .write("build/config.yaml", tld=tld)
        )
        result.to_export_safe()
        merged_text = read_file("build/config.yaml", tld=tld)

    print(merged_text)
    print(f"Steps: {', '.join(result.steps)}")


def demonstrate_terraform_handoff_workflow() -> None:
    """Show HCL data moving through raw text and Base64 transport."""
    print("\n=== Terraform Handoff Workflow ===\n")

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

    hcl_text = encode_hcl2(terraform)
    wrapped = base64_encode(hcl_text, wrap_raw_data=False)
    decoded_bytes = base64_decode(wrapped, unwrap_raw_data=False)

    print(hcl_text)
    print(f"\nTransport characters: {len(wrapped)}")
    print(f"Raw decoded bytes: {len(decoded_bytes)}")
    print(f"\nRound-tripped: {decode_hcl2(decoded_bytes) == terraform}")


def demonstrate_api_payload_workflow() -> None:
    """Normalize and serialize an API-style payload."""
    print("\n=== API Payload Workflow ===\n")

    payload = {
        "HTTPResponseCode": "200",
        "SelectedServices": ["api", "worker", "db", "api"],
        "Tags": ["api", "api", "docs"],
        "EmptyValue": "",
    }

    def select_services(data):
        return data | {"SelectedServices": ExtendedList(data["SelectedServices"]).filter_values(denylist=["db"])}

    workflow = (
        DataWorkflow.from_value(payload)
        .then(("select-services", select_services))
        .transform("reconstruct", "deduplicate", "compact", "unhump")
    )
    normalized = workflow.result().value

    with TemporaryDirectory() as tmpdir:
        tld = Path(tmpdir)
        write_file("build/payload.json", normalized, tld=tld)
        payload_text = read_file("build/payload.json", tld=tld)

    print(payload_text)
    print(f"Steps: {', '.join(workflow.steps)}")
    print(f"Known transforms: {', '.join(list_data_transform_steps())}")


def demonstrate_yaml_native_workflow() -> None:
    """Preserve YAML-native wrappers through the root file helpers."""
    print("\n=== YAML-Native Workflow ===\n")

    template = {
        "bucket_name": YamlTagged("!Ref", "BucketName"),
        "script": "echo one\necho two",
    }

    with TemporaryDirectory() as tmpdir:
        tld = Path(tmpdir)
        write_file("template.yaml", template, tld=tld)
        rendered = read_file("template.yaml", tld=tld)
        decoded = read_data_file("template.yaml", tld=tld)

    print(rendered)
    print(f"\nDecoded tag: {decoded['bucket_name'].tag}")


if __name__ == "__main__":
    demonstrate_layered_config_workflow()
    demonstrate_terraform_handoff_workflow()
    demonstrate_api_payload_workflow()
    demonstrate_yaml_native_workflow()
