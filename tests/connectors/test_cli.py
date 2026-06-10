"""Tests for unified CLI."""

from __future__ import annotations

import argparse
import json

from unittest.mock import MagicMock, patch

import pytest

from extended_data.connectors.cli import cmd_call, cmd_info, cmd_list, cmd_methods, main
from extended_data.containers import ExtendedDict


def test_cli_list():
    """Test the list command."""
    args = argparse.Namespace(json=False, available_only=False)
    with patch("sys.stdout.write") as mock_write:
        exit_code = cmd_list(args)
        assert exit_code == 0
        mock_write.assert_called()
        # Verify it lists some connectors
        output = "".join(call.args[0] for call in mock_write.call_args_list if call.args)
        assert "aws" in output
        assert "google" in output


def test_cli_list_json():
    """List command can emit machine-readable connector metadata."""
    args = argparse.Namespace(json=True, available_only=False)
    with patch("sys.stdout.write") as mock_write:
        exit_code = cmd_list(args)

    assert exit_code == 0
    output = mock_write.call_args.args[0]
    assert '"name": "github"' in output
    assert '"available":' in output
    assert "api_key_env" not in output


def test_cli_info():
    """Info command prints connector metadata."""
    args = argparse.Namespace(connector=" github ", json=False)
    with patch("sys.stdout.write") as mock_write:
        exit_code = cmd_info(args)

    assert exit_code == 0
    output = "".join(call.args[0] for call in mock_write.call_args_list if call.args)
    assert "name: github" in output
    assert "install: pip install extended-data[github]" in output


def test_cli_methods_lists_public_methods():
    """Methods command prints public callable methods with descriptions."""
    args = argparse.Namespace(connector="meshy")
    with patch("sys.stdout.write") as mock_write:
        exit_code = cmd_methods(args)

    assert exit_code == 0
    output = "".join(call.args[0] for call in mock_write.call_args_list if call.args)
    assert "request_data" in output
    assert "Decode an HTTP response body" in output


def test_cli_methods_json_lists_public_methods() -> None:
    """Methods command can emit machine-readable method metadata."""
    args = argparse.Namespace(connector="meshy", json=True)
    with patch("sys.stdout.write") as mock_write:
        exit_code = cmd_methods(args)

    assert exit_code == 0
    methods = json.loads(mock_write.call_args.args[0])
    decode_response = next(method for method in methods if method["name"] == "decode_response")
    assert decode_response["description"].startswith("Decode an HTTP response body")


def test_cli_call_parses_dynamic_keyword_arguments() -> None:
    """Call command accepts documented --arg value pairs after the method."""
    connector = MagicMock()
    connector.fetch.return_value = {"ok": True}

    with (
        patch("sys.argv", ["extended-data", "call", "example", "fetch", "--enabled", "true", "--count", "3"]),
        patch("extended_data.connectors.cli.get_connector", return_value=connector),
        patch("sys.stdout.write") as mock_write,
    ):
        exit_code = main()

    assert exit_code == 0
    connector.fetch.assert_called_once_with(enabled=True, count=3)
    output = "".join(call.args[0] for call in mock_write.call_args_list if call.args)
    assert '"ok": true' in output


def test_cli_call_accepts_json_flag_after_method() -> None:
    """Call command treats trailing --json as a CLI flag, not a method kwarg."""
    connector = MagicMock()
    connector.fetch.return_value = {"ok": True}
    args = argparse.Namespace(connector="example", method="fetch", extra=["--json"], json=False)

    with (
        patch("extended_data.connectors.cli.get_connector", return_value=connector),
        patch("sys.stdout.write") as mock_write,
    ):
        exit_code = cmd_call(args)

    assert exit_code == 0
    connector.fetch.assert_called_once_with()
    assert '"ok": true' in mock_write.call_args.args[0]


def test_cli_call_serializes_extended_containers_as_data() -> None:
    """Call command renders Tier 2 containers as JSON data, not iterable keys."""
    connector = MagicMock()
    connector.fetch.return_value = ExtendedDict({"service": {"name": "api"}})
    args = argparse.Namespace(connector="example", method="fetch", extra=[], json=True)

    with (
        patch("extended_data.connectors.cli.get_connector", return_value=connector),
        patch("sys.stdout.write") as mock_write,
    ):
        exit_code = cmd_call(args)

    assert exit_code == 0
    assert json.loads(mock_write.call_args.args[0]) == {"service": {"name": "api"}}


def test_cli_call_reports_missing_method() -> None:
    """Call command reports missing methods instead of failing silently."""
    args = argparse.Namespace(connector="example", method="missing", extra=[], json=False)
    connector = object()

    with (
        patch("extended_data.connectors.cli.get_connector", return_value=connector),
        patch("sys.stderr.write") as mock_write,
    ):
        exit_code = cmd_call(args)

    assert exit_code == 1
    assert "has no callable method" in mock_write.call_args.args[0]


def test_cli_call_reports_connector_errors() -> None:
    """Call command writes connector errors to stderr."""
    args = argparse.Namespace(connector="example", method="fetch", extra=[], json=False)

    with (
        patch("extended_data.connectors.cli.get_connector", side_effect=RuntimeError("boom")),
        patch("sys.stderr.write") as mock_write,
    ):
        exit_code = cmd_call(args)

    assert exit_code == 1
    assert "boom" in mock_write.call_args.args[0]


def test_cli_main_help():
    """Test main CLI entry point with help."""
    with patch("sys.argv", ["extended-data", "--help"]):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 0
