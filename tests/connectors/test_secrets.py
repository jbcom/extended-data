import json

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from extended_data.connectors.secrets import (
    ConfigInfo,
    OutputFormat,
    SecretsConnector,
    SyncOperation,
    SyncOptions,
    SyncResult,
)
from extended_data.connectors.secrets.tools import (
    RunPipelineSchema,
    dry_run,
    get_config_info,
    get_sources,
    get_targets,
    run_pipeline,
    validate_config,
)
from extended_data.containers import ExtendedDict, ExtendedList, ExtendedString


@pytest.fixture
def mock_logger() -> MagicMock:
    return MagicMock()


@pytest.fixture
def connector(mock_logger: MagicMock) -> SecretsConnector:
    # Force CLI mode by setting prefer_native=False
    return SecretsConnector(cli_path="/usr/bin/secretsync", prefer_native=False, logger=mock_logger)


def test_cli_get_config_info_valid(connector: SecretsConnector, tmp_path: Path) -> None:
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


def test_cli_get_config_info_not_found(connector: SecretsConnector) -> None:
    info = connector.get_config_info("/non/existent/path.yaml")
    assert info.valid is False
    assert "Configuration file not found" in info.error_message


def test_cli_get_config_info_invalid_yaml(connector: SecretsConnector, tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("invalid: yaml: :")

    info = connector.get_config_info(str(config_file))
    assert info.valid is False
    assert "Error parsing YAML file" in info.error_message


def test_cli_get_config_info_empty_file(connector: SecretsConnector, tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("")

    info = connector.get_config_info(str(config_file))
    assert info.valid is True
    assert info.source_count == 0


@patch("subprocess.run")
def test_cli_run_pipeline_operation(mock_run: MagicMock, connector: SecretsConnector) -> None:
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
    assert args.count("--output") == 1
    assert args[args.index("--output") + 1] == "json"


@patch("subprocess.run")
def test_cli_run_pipeline_diff_and_format(mock_run: MagicMock, connector: SecretsConnector) -> None:
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
    assert args.count("--output") == 1
    assert args[args.index("--output") + 1] == "json"


@patch("subprocess.run")
def test_cli_run_pipeline_default_output_is_json(mock_run: MagicMock, connector: SecretsConnector) -> None:
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps({"success": True}),
        stderr="",
    )

    result = connector.run_pipeline("config.yaml")

    assert result.success is True
    args = mock_run.call_args[0][0]
    assert args.count("--output") == 1
    assert args[args.index("--output") + 1] == "json"
    assert "--parallelism" not in args
    assert "--continue-on-error=true" in args


@patch("subprocess.run")
def test_cli_run_pipeline_parses_result_envelope(mock_run: MagicMock, connector: SecretsConnector) -> None:
    output = {
        "success": True,
        "target_count": 2,
        "secrets_processed": 5,
        "secrets_added": 1,
        "secrets_modified": 2,
        "secrets_removed": 0,
        "secrets_unchanged": 2,
        "duration_ms": 321,
        "results": [
            {"target": "prod", "phase": "merge", "success": True},
            {"target": "prod", "phase": "sync", "success": True},
        ],
        "diff_output": '{"summary":{"added":1}}',
        "diff": {"dry_run": True},
    }
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps(output),
        stderr="",
    )

    result = connector.run_pipeline("config.yaml")

    assert result.success is True
    assert result.target_count == 2
    assert result.secrets_processed == 5
    assert result.secrets_added == 1
    assert result.secrets_modified == 2
    assert result.secrets_unchanged == 2
    assert result.duration_ms == 321
    assert json.loads(result.results_json) == output["results"]
    assert result.diff_output == '{"summary":{"added":1}}'


@patch("subprocess.run")
def test_cli_run_pipeline_rejects_legacy_raw_diff_json(mock_run: MagicMock, connector: SecretsConnector) -> None:
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps(
            {
                "dry_run": True,
                "summary": {"added": 1, "modified": 0, "removed": 0, "unchanged": 0},
                "targets": [],
            }
        ),
        stderr="",
    )

    result = connector.run_pipeline("config.yaml", SyncOptions(dry_run=True, compute_diff=True))

    assert result.success is False
    assert "expected pipeline result envelope" in result.error_message


@patch("subprocess.run")
def test_cli_run_pipeline_parses_failure_result_envelope(mock_run: MagicMock, connector: SecretsConnector) -> None:
    mock_run.return_value = MagicMock(
        returncode=1,
        stdout=json.dumps(
            {
                "success": False,
                "target_count": 1,
                "secrets_processed": 2,
                "error_message": "pipeline completed with errors",
                "results": [{"target": "prod", "phase": "sync", "success": False, "error": "denied"}],
            }
        ),
        stderr="Error: pipeline completed with errors\n",
    )

    result = connector.run_pipeline("config.yaml")

    assert result.success is False
    assert result.target_count == 1
    assert result.secrets_processed == 2
    assert result.error_message == "pipeline completed with errors"
    assert json.loads(result.results_json)[0]["error"] == "denied"


@patch("subprocess.run")
def test_cli_run_pipeline_failure_envelope_uses_stderr_when_error_message_missing(
    mock_run: MagicMock,
    connector: SecretsConnector,
) -> None:
    mock_run.return_value = MagicMock(
        returncode=1,
        stdout=json.dumps({"success": False, "results": []}),
        stderr="Error: boom\n",
    )

    result = connector.run_pipeline("config.yaml")

    assert result.success is False
    assert result.error_message == "Error: boom\n"


@patch("subprocess.run")
def test_cli_run_pipeline_success_without_json_is_error(mock_run: MagicMock, connector: SecretsConnector) -> None:
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="",
        stderr="",
    )

    result = connector.run_pipeline("config.yaml")

    assert result.success is False
    assert "produced no JSON output" in result.error_message


@patch("subprocess.run")
def test_cli_run_pipeline_non_json_failure_uses_cli_output(mock_run: MagicMock, connector: SecretsConnector) -> None:
    mock_run.return_value = MagicMock(
        returncode=1,
        stdout="not json",
        stderr="",
    )

    result = connector.run_pipeline("config.yaml")

    assert result.success is False
    assert result.error_message == "not json"


@patch("subprocess.run")
def test_cli_run_pipeline_only_emits_supported_cli_flags(mock_run: MagicMock, connector: SecretsConnector) -> None:
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout=json.dumps({"success": True}),
        stderr="",
    )

    options = SyncOptions(
        targets=["prod", "staging"],
        continue_on_error=False,
        parallelism=12,
    )
    connector.run_pipeline("config.yaml", options)

    args = mock_run.call_args[0][0]
    assert "--targets" in args
    assert args[args.index("--targets") + 1] == "prod,staging"
    assert "--parallelism" in args
    assert args[args.index("--parallelism") + 1] == "12"
    assert "--continue-on-error=false" in args


@patch("subprocess.run")
def test_cli_validate_config(mock_run: MagicMock, connector: SecretsConnector) -> None:
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


@patch("extended_data.connectors.secrets.SecretsConnector")
def test_run_pipeline_tool_default_continue_on_error_matches_cli(mock_connector_class: MagicMock) -> None:
    mock_connector = mock_connector_class.return_value
    mock_connector.run_pipeline.return_value = SyncResult(success=True, secrets_processed=3)

    result = run_pipeline("config.yaml")

    options = mock_connector.run_pipeline.call_args.args[1]
    assert isinstance(options, SyncOptions)
    assert options.continue_on_error is True
    assert isinstance(result, ExtendedDict)
    assert isinstance(result["secrets_processed"], int)
    assert result["success"] is True
    assert result["secrets_processed"] == 3


@patch("extended_data.connectors.secrets.SecretsConnector")
def test_run_pipeline_tool_can_disable_continue_on_error(mock_connector_class: MagicMock) -> None:
    mock_connector = mock_connector_class.return_value
    mock_connector.run_pipeline.return_value = SyncResult(success=True)

    run_pipeline("config.yaml", continue_on_error=False)

    options = mock_connector.run_pipeline.call_args.args[1]
    assert isinstance(options, SyncOptions)
    assert options.continue_on_error is False


def test_run_pipeline_schema_default_continue_on_error_matches_cli() -> None:
    schema = RunPipelineSchema(config_path="config.yaml")

    assert schema.continue_on_error is True


@patch("extended_data.connectors.secrets.SecretsConnector")
def test_validate_config_tool_returns_extended_payload(mock_connector_class: MagicMock) -> None:
    mock_connector = mock_connector_class.return_value
    mock_connector.validate_config.return_value = (True, "valid config")

    result = validate_config("config.yaml")

    assert isinstance(result, ExtendedDict)
    assert isinstance(result["message"], ExtendedString)
    assert result["valid"] is True
    assert result["config_path"] == "config.yaml"


@patch("extended_data.connectors.secrets.SecretsConnector")
def test_dry_run_tool_returns_extended_payload(mock_connector_class: MagicMock) -> None:
    mock_connector = mock_connector_class.return_value
    mock_connector.dry_run.return_value = SyncResult(
        success=True,
        target_count=2,
        secrets_added=1,
        secrets_modified=2,
        secrets_removed=0,
        secrets_unchanged=3,
        diff_output="diff",
    )

    result = dry_run("config.yaml")

    assert isinstance(result, ExtendedDict)
    assert isinstance(result["diff_output"], ExtendedString)
    assert result["secrets_would_add"] == 1


@patch("extended_data.connectors.secrets.SecretsConnector")
def test_get_config_info_tool_returns_extended_payload(mock_connector_class: MagicMock) -> None:
    mock_connector = mock_connector_class.return_value
    mock_connector.get_config_info.return_value = ConfigInfo(
        valid=True,
        source_count=1,
        target_count=1,
        sources=["vault/prod"],
        targets=["aws/prod"],
        has_merge_store=True,
        vault_address="https://vault.example.com",
        aws_region="us-east-1",
    )

    result = get_config_info("config.yaml")

    assert isinstance(result, ExtendedDict)
    assert isinstance(result["sources"], ExtendedList)
    assert isinstance(result["sources"][0], ExtendedString)
    assert result["targets"] == ["aws/prod"]


@patch("extended_data.connectors.secrets.SecretsConnector")
def test_get_targets_tool_returns_extended_payload(mock_connector_class: MagicMock) -> None:
    mock_connector = mock_connector_class.return_value
    mock_connector.get_targets.return_value = (["prod", "dev"], "")

    result = get_targets("config.yaml")

    assert isinstance(result, ExtendedDict)
    assert isinstance(result["targets"], ExtendedList)
    assert isinstance(result["targets"][0], ExtendedString)
    assert result["count"] == 2


@patch("extended_data.connectors.secrets.SecretsConnector")
def test_get_sources_tool_returns_extended_payload(mock_connector_class: MagicMock) -> None:
    mock_connector = mock_connector_class.return_value
    mock_connector.get_sources.return_value = (["vault/prod"], "")

    result = get_sources("config.yaml")

    assert isinstance(result, ExtendedDict)
    assert isinstance(result["sources"], ExtendedList)
    assert isinstance(result["sources"][0], ExtendedString)
    assert result["count"] == 1
