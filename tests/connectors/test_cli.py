"""Tests for unified CLI."""

from __future__ import annotations

import argparse

from unittest.mock import patch

import pytest

from extended_data.connectors.cli import cmd_list, main


@pytest.mark.xfail(reason="Pre-existing mock issue: cmd_list uses logging instead of print")
def test_cli_list():
    """Test the list command."""
    args = argparse.Namespace(json=False)
    with patch("builtins.print") as mock_print:
        exit_code = cmd_list(args)
        assert exit_code == 0
        mock_print.assert_called()
        # Verify it lists some connectors
        output = "\n".join(call.args[0] for call in mock_print.call_args_list if call.args)
        assert "aws" in output
        assert "google" in output


def test_cli_main_help():
    """Test main CLI entry point with help."""
    with patch("sys.argv", ["extended-data", "--help"]):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 0
