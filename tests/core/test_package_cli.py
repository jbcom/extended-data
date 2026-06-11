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


def test_connector_commands_delegate_to_connector_cli() -> None:
    """Existing connector commands remain available from the package entrypoint."""
    with patch("extended_data.connectors.cli.main", return_value=7) as mock_main:
        exit_code = cli_module.main(["list", "--json"])

    assert exit_code == 7
    mock_main.assert_called_once_with(["list", "--json"])
