import json

from unittest.mock import MagicMock, patch

import pytest
import yaml

from extended_data.connectors.secrets import (
    OutputFormat,
    SecretsConnector,
    SyncOperation,
    SyncOptions,
)


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def connector(mock_logger):
    # Force CLI mode by setting prefer_native=False
    return SecretsConnector(cli_path="/usr/bin/secretsync", prefer_native=False, logger=mock_logger)


def test_cli_get_config_info_valid(connector, tmp_path):
    config_file = tmp_path / "config.yaml"
    config_data = {
        "sources": {"src1": {}, "src2": {}},
        "targets": {"tgt1": {}},
        "vault": {"address": "http://vault:8200"},
        "aws": {"region": "us-east-1"},
        "merge_store": {},
    }
    config_file.write_text(yaml.dump(config_data))

    info = connector.get_config_info(str(config_file))

    assert info.valid is True
    assert info.source_count == 2
    assert info.target_count == 1
    assert "src1" in info.sources
    assert "src2" in info.sources
    assert "tgt1" in info.targets
    assert info.has_merge_store is True
    assert info.vault_address == "http://vault:8200"
    assert info.aws_region == "us-east-1"


def test_cli_get_config_info_not_found(connector):
    info = connector.get_config_info("/non/existent/path.yaml")
    assert info.valid is False
    assert "Configuration file not found" in info.error_message


def test_cli_get_config_info_invalid_yaml(connector, tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("invalid: yaml: :")

    info = connector.get_config_info(str(config_file))
    assert info.valid is False
    assert "Error parsing YAML file" in info.error_message


def test_cli_get_config_info_empty_file(connector, tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("")

    info = connector.get_config_info(str(config_file))
    assert info.valid is True
    assert info.source_count == 0


@patch("subprocess.run")
def test_cli_run_pipeline_operation(mock_run, connector):
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps({"success": True, "secrets_processed": 5}),
        stderr="",
    )

    options = SyncOptions(operation=SyncOperation.MERGE)
    result = connector.run_pipeline("config.yaml", options)

    assert result.success is True
    assert result.secrets_processed == 5

    # Check that it uses "pipeline" command with "--merge-only" flag
    args = mock_run.call_args[0][0]
    assert args[1] == "pipeline"
    assert "--merge-only" in args


@patch("subprocess.run")
def test_cli_run_pipeline_diff_and_format(mock_run, connector):
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps({"success": True, "diff_output": "some diff"}),
        stderr="",
    )

    options = SyncOptions(
        compute_diff=True,
        output_format=OutputFormat.JSON,
    )
    result = connector.run_pipeline("config.yaml", options)

    assert result.success is True

    args = mock_run.call_args[0][0]
    assert "--diff" in args
    assert "--output" in args
    assert "json" in args


@patch("subprocess.run")
def test_cli_validate_config(mock_run, connector):
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="Valid",
        stderr="",
    )

    is_valid, message = connector.validate_config("config.yaml")
    assert is_valid is True
    assert "valid" in message.lower()

    args = mock_run.call_args[0][0]
    assert "validate" in args
