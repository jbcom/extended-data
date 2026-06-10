"""Secrets Connector - enterprise-grade SecretSync integration.

This connector integrates with the standalone SecretSync project
(`jbcom/secrets-sync`), enabling enterprise-grade secret synchronization from
HashiCorp Vault to AWS Secrets Manager with two-phase architecture,
inheritance, versioning, and CI/CD integration.

The connector executes the supported `secretsync` subprocess CLI contract.
Alternate runtime adapters should be added only after SecretSync publishes a
stable adapter contract.

Example usage:
    from extended_data.connectors.secrets import SecretsConnector

    # Initialize connector
    connector = SecretsConnector()

    # Validate a configuration
    validation = connector.validate_config("pipeline.yaml")

    # Run a dry-run to see what would change
    result = connector.dry_run("pipeline.yaml")
    print(f"Would sync {result['secrets_processed']} secrets")

    # Execute the full pipeline
    result = connector.run_pipeline("pipeline.yaml")
    if result["success"]:
        print(f"Synced {result['secrets_added']} secrets")
"""

from __future__ import annotations

import json
import shutil
import subprocess

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from extended_data.connectors.base import VendorConnectorBase
from extended_data.containers import ExtendedDict, extend_data
from extended_data.logging import Logging


class SyncOperation(str, Enum):
    """Pipeline operation types."""

    MERGE = "merge"
    SYNC = "sync"
    PIPELINE = "pipeline"


class OutputFormat(str, Enum):
    """Output format for diff display."""

    HUMAN = "human"
    JSON = "json"
    GITHUB = "github"
    COMPACT = "compact"
    SIDE_BY_SIDE = "side-by-side"


@dataclass
class SyncOptions:
    """Options for pipeline execution."""

    dry_run: bool = False
    operation: SyncOperation = SyncOperation.PIPELINE
    targets: list[str] = field(default_factory=list)
    continue_on_error: bool = True
    parallelism: int = 0
    compute_diff: bool = False
    output_format: OutputFormat = OutputFormat.JSON


@dataclass
class SyncResult:
    """Result of a sync operation."""

    success: bool = False
    target_count: int = 0
    secrets_processed: int = 0
    secrets_added: int = 0
    secrets_modified: int = 0
    secrets_removed: int = 0
    secrets_unchanged: int = 0
    duration_ms: int = 0
    error_message: str = ""
    results_json: str = ""
    diff_output: str = ""

    @classmethod
    def from_cli_output(cls, output: dict[str, Any]) -> SyncResult:
        """Create from CLI JSON output."""
        return cls(
            success=output.get("success", False),
            target_count=output.get("target_count", 0),
            secrets_processed=output.get("secrets_processed", 0),
            secrets_added=output.get("secrets_added", 0),
            secrets_modified=output.get("secrets_modified", 0),
            secrets_removed=output.get("secrets_removed", 0),
            secrets_unchanged=output.get("secrets_unchanged", 0),
            duration_ms=output.get("duration_ms", 0),
            error_message=output.get("error_message", ""),
            results_json=json.dumps(output.get("results", [])),
            diff_output=output.get("diff_output", ""),
        )

    def to_dict(self) -> ExtendedDict:
        """Return an extended sync result payload."""
        return extend_data(asdict(self))


@dataclass
class ConfigInfo:
    """Information about a pipeline configuration."""

    valid: bool = False
    error_message: str = ""
    source_count: int = 0
    target_count: int = 0
    sources: list[str] = field(default_factory=list)
    targets: list[str] = field(default_factory=list)
    has_merge_store: bool = False
    vault_address: str = ""
    aws_region: str = ""

    def to_dict(self) -> ExtendedDict:
        """Return an extended config info payload."""
        return extend_data(asdict(self))


class SecretsConnector(VendorConnectorBase):
    """Enterprise-grade SecretSync connector.

    This connector wraps the standalone SecretSync project
    (`jbcom/secrets-sync`) through the supported `secretsync` CLI.

    Features:
    - Two-phase pipeline architecture (merge → sync)
    - Secret inheritance and deep merging
    - AWS Organizations discovery
    - Dry-run with visual diff output
    - CI/CD integration with exit codes

    Alternate runtime adapters are intentionally not accepted here until
    SecretSync publishes a stable adapter contract.
    """

    def __init__(
        self,
        cli_path: str | None = None,
        logger: Logging | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the secrets connector.

        Args:
            cli_path: Path to secretsync CLI binary (for CLI mode)
            logger: Logger instance
            **kwargs: Passed to VendorConnectorBase
        """
        super().__init__(logger=logger, **kwargs)

        self._cli_path = cli_path or self._find_cli()

        self.logger.info("SecretsConnector initialized in CLI mode")

    def _find_cli(self) -> str | None:
        """Find the SecretSync `secretsync` CLI binary."""
        # Check common locations
        candidates = [
            "secretsync",
            "/usr/local/bin/secretsync",
            "/usr/bin/secretsync",
            str(Path.home() / "go" / "bin" / "secretsync"),
        ]

        for candidate in candidates:
            if shutil.which(candidate):
                return candidate

        return None

    @property
    def cli_available(self) -> bool:
        """Check if CLI is available."""
        return self._cli_path is not None

    def validate_config(self, config_path: str) -> ExtendedDict:
        """Validate a pipeline configuration file.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            Extended validation payload.
        """
        is_valid, message = self._cli_validate_config(config_path)

        return extend_data({
            "valid": is_valid,
            "message": message,
            "config_path": config_path,
        })

    def _cli_validate_config(self, config_path: str) -> tuple[bool, str]:
        """Validate config via CLI."""
        if not self._cli_path:
            return False, "CLI not available"

        try:
            result = subprocess.run(
                [self._cli_path, "validate", "--config", config_path],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if result.returncode == 0:
                return True, "Configuration is valid"
            return False, result.stderr or result.stdout
        except subprocess.TimeoutExpired:
            return False, "Validation timed out"
        except Exception as e:
            return False, str(e)

    def get_config_info(self, config_path: str) -> ExtendedDict:
        """Get detailed information about a configuration.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            Extended configuration details payload.
        """
        return self._cli_get_config_info(config_path).to_dict()

    def _cli_get_config_info(self, config_path: str) -> ConfigInfo:
        """Get config info via CLI."""
        try:
            import yaml
        except ImportError:
            return ConfigInfo(error_message="pyyaml is required for CLI mode but not installed.")

        try:
            with open(config_path) as f:
                cfg = yaml.safe_load(f)

            if not isinstance(cfg, dict):
                # Handles empty file (cfg=None) or non-dict root
                cfg = {}

            return ConfigInfo(
                valid=True,
                source_count=len(cfg.get("sources", {})),
                target_count=len(cfg.get("targets", {})),
                sources=list(cfg.get("sources", {}).keys()),
                targets=list(cfg.get("targets", {}).keys()),
                has_merge_store="merge_store" in cfg,
                vault_address=cfg.get("vault", {}).get("address", ""),
                aws_region=cfg.get("aws", {}).get("region", ""),
            )
        except FileNotFoundError:
            return ConfigInfo(error_message=f"Configuration file not found: {config_path}")
        except yaml.YAMLError as e:
            return ConfigInfo(error_message=f"Error parsing YAML file: {e}")

    def run_pipeline(
        self,
        config_path: str,
        options: SyncOptions | None = None,
    ) -> ExtendedDict:
        """Execute the secrets synchronization pipeline.

        Args:
            config_path: Path to YAML configuration file
            options: Execution options (defaults to full pipeline)

        Returns:
            Extended sync result payload.
        """
        options = options or SyncOptions()

        return self._cli_run_pipeline(config_path, options).to_dict()

    def _cli_run_pipeline(
        self,
        config_path: str,
        options: SyncOptions,
    ) -> SyncResult:
        """Run pipeline via CLI."""
        if not self._cli_path:
            return SyncResult(
                success=False,
                error_message="secretsync CLI not available",
            )

        # Always request JSON so this Python surface can reliably return a
        # structured SyncResult from the supported CLI contract.
        cmd = [
            self._cli_path,
            "pipeline",
            "--config",
            config_path,
            "--output",
            "json",
        ]

        if options.operation == SyncOperation.MERGE:
            cmd.append("--merge-only")
        elif options.operation == SyncOperation.SYNC:
            cmd.append("--sync-only")

        if options.dry_run:
            cmd.append("--dry-run")
        if options.compute_diff:
            cmd.append("--diff")
        if options.targets:
            cmd.extend(["--targets", ",".join(options.targets)])
        cmd.append(f"--continue-on-error={str(options.continue_on_error).lower()}")
        if options.parallelism > 0:
            cmd.extend(["--parallelism", str(options.parallelism)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
                check=False,
            )

            stdout = result.stdout.strip()
            if stdout:
                try:
                    output = json.loads(stdout)
                except json.JSONDecodeError as e:
                    if result.returncode == 0:
                        return SyncResult(
                            success=False,
                            error_message=f"Failed to parse output: {e}",
                        )
                else:
                    if not isinstance(output, dict) or "success" not in output:
                        return SyncResult(
                            success=False,
                            error_message=(
                                "Unsupported secretsync JSON output: expected pipeline result envelope. "
                                "Upgrade secretsync to a version that emits the stable result envelope."
                            ),
                        )
                    parsed = SyncResult.from_cli_output(output)
                    if result.returncode != 0 and not parsed.error_message:
                        parsed.error_message = result.stderr or f"secretsync exited with status {result.returncode}"
                    return parsed

            if result.returncode == 0:
                return SyncResult(
                    success=False,
                    error_message="secretsync produced no JSON output",
                )

            return SyncResult(
                success=False,
                error_message=result.stderr or result.stdout,
            )
        except subprocess.TimeoutExpired:
            return SyncResult(
                success=False,
                error_message="Pipeline execution timed out",
            )
        except json.JSONDecodeError as e:
            return SyncResult(
                success=False,
                error_message=f"Failed to parse output: {e}",
            )
        except Exception as e:
            return SyncResult(
                success=False,
                error_message=str(e),
            )

    def dry_run(self, config_path: str) -> ExtendedDict:
        """Perform a dry run of the pipeline.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            Extended dry-run result payload.
        """
        options = SyncOptions(dry_run=True, compute_diff=True)
        return self._cli_run_pipeline(config_path, options).to_dict()

    def merge(self, config_path: str, dry_run: bool = False) -> ExtendedDict:
        """Run only the merge phase of the pipeline.

        Args:
            config_path: Path to YAML configuration file
            dry_run: If True, don't make actual changes

        Returns:
            Extended merge result payload.
        """
        options = SyncOptions(
            operation=SyncOperation.MERGE,
            dry_run=dry_run,
            compute_diff=dry_run,
        )
        return self._cli_run_pipeline(config_path, options).to_dict()

    def sync(self, config_path: str, dry_run: bool = False) -> ExtendedDict:
        """Run only the sync phase of the pipeline.

        Args:
            config_path: Path to YAML configuration file
            dry_run: If True, don't make actual changes

        Returns:
            Extended sync result payload.
        """
        options = SyncOptions(
            operation=SyncOperation.SYNC,
            dry_run=dry_run,
            compute_diff=dry_run,
        )
        return self._cli_run_pipeline(config_path, options).to_dict()

    def get_targets(self, config_path: str) -> ExtendedDict:
        """Get the list of targets from a configuration.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            Extended targets payload.
        """
        info = self.get_config_info(config_path)
        targets = info.get("targets", [])
        return extend_data({
            "targets": targets,
            "count": len(targets),
            "error_message": info.get("error_message", ""),
        })

    def get_sources(self, config_path: str) -> ExtendedDict:
        """Get the list of sources from a configuration.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            Extended sources payload.
        """
        info = self.get_config_info(config_path)
        sources = info.get("sources", [])
        return extend_data({
            "sources": sources,
            "count": len(sources),
            "error_message": info.get("error_message", ""),
        })


# Import tools for AI framework integration
from extended_data.connectors.secrets.tools import (
    get_crewai_tools,
    get_langchain_tools,
    get_strands_tools,
    get_tools,
)


__all__ = [
    "ConfigInfo",
    "OutputFormat",
    # Core classes
    "SecretsConnector",
    "SyncOperation",
    "SyncOptions",
    "SyncResult",
    "get_crewai_tools",
    "get_langchain_tools",
    "get_strands_tools",
    # Tools
    "get_tools",
]
