"""Tests for the top-level Extended Data CLI."""

from __future__ import annotations

import json

from unittest.mock import patch

from extended_data import cli as cli_module


def _stdout_text(mock_write) -> str:
    """Return concatenated stdout writes from a patched writer."""
    return "".join(call.args[0] for call in mock_write.call_args_list if call.args)


def test_decode_inline_json_exports_through_datafile_boundary() -> None:
    """The top-level CLI should expose Tier 3 decode/export utilities."""
    with patch("sys.stdout.write") as mock_write:
        exit_code = cli_module.main(["decode", '{"service": {"name": "api"}}', "--suffix", "json"])

    assert exit_code == 0
    assert json.loads(_stdout_text(mock_write)) == {"service": {"name": "api"}}


def test_decode_file_can_export_yaml(tmp_path) -> None:
    """File decoding should use DataFile and the shared export boundary."""
    config = tmp_path / "service.json"
    config.write_text('{"service": {"name": "api"}}', encoding="utf-8")

    with patch("sys.stdout.write") as mock_write:
        exit_code = cli_module.main(["decode", "--file", str(config), "--output", "yaml"])

    assert exit_code == 0
    output = _stdout_text(mock_write)
    assert "service:" in output
    assert "name: api" in output


def test_decode_requires_one_input_source() -> None:
    """Decode should fail clearly when no inline value or file path is supplied."""
    with patch("sys.stderr.write") as mock_write:
        exit_code = cli_module.main(["decode"])

    assert exit_code == 1
    assert "pass VALUE or --file" in _stdout_text(mock_write)


def test_decode_rejects_ambiguous_input_sources(tmp_path) -> None:
    """Decode should not guess when both inline and file input are supplied."""
    config = tmp_path / "service.json"
    config.write_text('{"service": "api"}', encoding="utf-8")

    with patch("sys.stderr.write") as mock_write:
        exit_code = cli_module.main(["decode", "{}", "--file", str(config)])

    assert exit_code == 1
    assert "pass either VALUE or --file" in _stdout_text(mock_write)


def test_inspect_file_exports_datafile_metadata(tmp_path) -> None:
    """Inspect should expose the same promoted metadata DataFile carries."""
    config = tmp_path / "service.yaml"
    config.write_text("service:\n  name: api\n", encoding="utf-8")

    with patch("sys.stdout.write") as mock_write:
        exit_code = cli_module.main(["inspect", "--file", str(config)])

    assert exit_code == 0
    metadata = json.loads(_stdout_text(mock_write))
    assert metadata["source"] == str(config)
    assert metadata["encoding"] == "yaml"
    assert metadata["path"] == str(config.resolve())
    assert metadata["is_url"] is False
    assert metadata["data_type"] == "ExtendedDict"


def test_inspect_inline_payload_reports_memory_source() -> None:
    """Inline inspect keeps in-memory payload provenance explicit."""
    with patch("sys.stdout.write") as mock_write:
        exit_code = cli_module.main(["inspect", '{"service": "api"}', "--suffix", "json"])

    assert exit_code == 0
    metadata = json.loads(_stdout_text(mock_write))
    assert metadata["source"] == "memory"
    assert metadata["encoding"] == "json"
    assert metadata["path"] is None
    assert metadata["data_type"] == "ExtendedDict"


def test_inspect_rejects_ambiguous_input_sources(tmp_path) -> None:
    """Inspect should share decode's explicit source selection behavior."""
    config = tmp_path / "service.json"
    config.write_text('{"service": "api"}', encoding="utf-8")

    with patch("sys.stderr.write") as mock_write:
        exit_code = cli_module.main(["inspect", "{}", "--file", str(config)])

    assert exit_code == 1
    assert "pass either VALUE or --file" in _stdout_text(mock_write)


def test_removed_connector_commands_are_not_top_level_cli_commands() -> None:
    """The base package CLI should not delegate to the split vendor package."""
    with patch("sys.stderr.write") as mock_write:
        try:
            cli_module.main(["list", "--json"])
        except SystemExit as exc:
            exit_code = int(exc.code)
        else:
            exit_code = 0

    assert exit_code == 2
    assert "invalid choice" in _stdout_text(mock_write)


def test_merge_files_exports_deep_merged_workflow_result(tmp_path) -> None:
    """The top-level CLI should expose a DataWorkflow-backed merge command."""
    base = tmp_path / "base.yaml"
    env = tmp_path / "env.yaml"
    base.write_text("service:\n  name: api\n  debug: false\nports:\n  - 8080\n", encoding="utf-8")
    env.write_text("service:\n  debug: true\nports:\n  - 8081\n", encoding="utf-8")

    with patch("sys.stdout.write") as mock_write:
        exit_code = cli_module.main(["merge", str(base), str(env), "--output", "json"])

    assert exit_code == 0
    assert json.loads(_stdout_text(mock_write)) == {
        "service": {"name": "api", "debug": True},
        "ports": [8080, 8081],
    }


def test_merge_files_can_write_output_artifact(tmp_path) -> None:
    """Merged workflow output can be written through the shared file boundary."""
    base = tmp_path / "base.json"
    env = tmp_path / "env.json"
    output = tmp_path / "build" / "service.yaml"
    base.write_text('{"service": {"name": "api", "debug": false}}', encoding="utf-8")
    env.write_text('{"service": {"debug": true}}', encoding="utf-8")

    with patch("sys.stdout.write") as mock_write:
        exit_code = cli_module.main(["merge", str(base), str(env), "--output", "yaml", "--write", str(output)])

    assert exit_code == 0
    output_text = output.read_text(encoding="utf-8")
    assert _stdout_text(mock_write) == f"{output_text}\n"
    assert "debug: true" in output_text


def test_merge_requires_multiple_files(tmp_path) -> None:
    """Merge should fail loudly instead of treating a single file as a workflow."""
    base = tmp_path / "base.json"
    base.write_text('{"service": "api"}', encoding="utf-8")

    with patch("sys.stderr.write") as mock_write:
        exit_code = cli_module.main(["merge", str(base)])

    assert exit_code == 1
    assert "merge requires at least two files" in _stdout_text(mock_write)


def test_transform_file_applies_ordered_tier2_steps(tmp_path) -> None:
    """Transform should expose common Tier 2 operations through DataWorkflow."""
    payload = tmp_path / "payload.json"
    payload.write_text(
        '{"HTTPResponseCode": "200", "SelectedServices": ["api", "api", "worker"], "EmptyValue": ""}',
        encoding="utf-8",
    )

    with patch("sys.stdout.write") as mock_write:
        exit_code = cli_module.main(
            [
                "transform",
                "--file",
                str(payload),
                "--step",
                "reconstruct",
                "--step",
                "unhump",
                "--step",
                "deduplicate",
                "--step",
                "compact",
            ]
        )

    assert exit_code == 0
    assert json.loads(_stdout_text(mock_write)) == {
        "http_response_code": 200,
        "selected_services": ["api", "worker"],
    }


def test_transform_inline_string_applies_string_primitives() -> None:
    """String-specific transforms should be available from the package CLI."""
    with patch("sys.stdout.write") as mock_write:
        exit_code = cli_module.main(
            [
                "transform",
                "API Response Value",
                "--suffix",
                "raw",
                "--step",
                "to-snake-case",
                "--output",
                "raw",
            ]
        )

    assert exit_code == 0
    assert _stdout_text(mock_write) == "api_response_value\n"


def test_transform_inline_string_can_reconstruct_scalar() -> None:
    """Scalar reconstruction should use the string primitive when needed."""
    with patch("sys.stdout.write") as mock_write:
        exit_code = cli_module.main(["transform", "200", "--suffix", "raw", "--step", "reconstruct"])

    assert exit_code == 0
    assert json.loads(_stdout_text(mock_write)) == 200


def test_transform_requires_at_least_one_step(tmp_path) -> None:
    """Transform should fail clearly when no primitive/container step is requested."""
    payload = tmp_path / "payload.json"
    payload.write_text('{"service": "api"}', encoding="utf-8")

    with patch("sys.stderr.write") as mock_write:
        exit_code = cli_module.main(["transform", "--file", str(payload)])

    assert exit_code == 1
    assert "transform requires at least one --step" in _stdout_text(mock_write)


def test_transform_reports_step_that_does_not_match_data_shape() -> None:
    """Shape-specific transforms should fail loudly instead of silently lowering data."""
    with patch("sys.stderr.write") as mock_write:
        exit_code = cli_module.main(["transform", '["api"]', "--suffix", "json", "--step", "unhump"])

    assert exit_code == 1
    assert "transform 'unhump' is not available for ExtendedList" in _stdout_text(mock_write)


def test_transform_can_write_output_artifact(tmp_path) -> None:
    """Transformed workflow output can be written through the shared file boundary."""
    payload = tmp_path / "payload.json"
    output = tmp_path / "build" / "payload.yaml"
    payload.write_text('{"HTTPResponseCode": "200"}', encoding="utf-8")

    with patch("sys.stdout.write") as mock_write:
        exit_code = cli_module.main(
            [
                "transform",
                "--file",
                str(payload),
                "--step",
                "reconstruct",
                "--step",
                "unhump",
                "--output",
                "yaml",
                "--write",
                str(output),
            ]
        )

    assert exit_code == 0
    output_text = output.read_text(encoding="utf-8")
    assert _stdout_text(mock_write) == f"{output_text}\n"
    assert "http_response_code: 200" in output_text
