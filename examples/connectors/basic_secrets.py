#!/usr/bin/env python3
"""Example: SecretSync connector usage.

This example demonstrates the `extended-data[secrets]` bridge to the
standalone `jbcom/secrets-sync` CLI.

Requirements:
    pip install extended-data[secrets]
    secretsync must be installed on PATH

Run:
    uv run python examples/connectors/basic_secrets.py pipeline.yaml
"""

from __future__ import annotations

import sys

from pathlib import Path

from extended_data import ConnectorFabric, OutputFormat, SyncOptions


def main() -> int:
    """Inspect a SecretSync pipeline config and run a dry-run through the CLI contract."""
    fabric = ConnectorFabric()
    info = fabric.get_connector_info("secrets")
    if not info["available"]:
        print(f"Error: SecretSync connector is unavailable. Install with: {info['install']}")
        if info["missing"]:
            print(f"Missing packages: {', '.join(info['missing'])}")
        return 1

    config_path = Path(sys.argv[1] if len(sys.argv) > 1 else "pipeline.yaml")
    connector = fabric.get_connector("secrets")

    print(f"Inspecting SecretSync config: {config_path}")
    config_info = connector.get_config_info(str(config_path))
    if not config_info["valid"]:
        print(f"Error: {config_info['error_message']}")
        return 1

    print(
        "Config summary: "
        f"{config_info['source_count']} source(s), "
        f"{config_info['target_count']} target(s), "
        f"merge store={config_info['has_merge_store']}",
    )

    if not connector.cli_available:
        print("Error: secretsync CLI not available on PATH.")
        print("Install jbcom/secrets-sync and re-run this example to exercise the dry-run contract.")
        return 1

    result = connector.run_pipeline(
        str(config_path),
        SyncOptions(dry_run=True, compute_diff=True, output_format=OutputFormat.JSON),
    )

    if not result["success"]:
        print("Error: secretsync dry run failed.")
        print("Run secretsync directly in a secure terminal for full diagnostics.")
        print("The CLI must emit the stable `secretsync pipeline --output json` result envelope.")
        return 1

    print("Dry run completed successfully.")
    if result["diff_output"]:
        print("Diff output was returned by secretsync and is not printed because it may contain secret values.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
