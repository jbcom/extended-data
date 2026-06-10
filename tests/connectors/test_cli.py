"""Tests for unified CLI."""

from __future__ import annotations

import argparse

from unittest.mock import patch

import pytest

from extended_data.connectors.cli import cmd_info, cmd_list, cmd_methods, main


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


def test_cli_main_help():
    """Test main CLI entry point with help."""
    with patch("sys.argv", ["extended-data", "--help"]):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 0
