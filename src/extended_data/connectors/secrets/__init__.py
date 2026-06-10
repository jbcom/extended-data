"""Secrets Connector - Enterprise-grade secret synchronization.

This connector provides Python bindings for secretssync, enabling
enterprise-grade secret synchronization from HashiCorp Vault to
AWS Secrets Manager with two-phase architecture, inheritance,
versioning, and CI/CD integration.

The connector can operate in two modes:
1. Native mode: Uses gopy-generated Python bindings for maximum performance
2. CLI mode: Falls back to subprocess calls if bindings aren't available

Example usage:
    from extended_data.connectors.secrets import SecretsConnector

    # Initialize connector
    connector = SecretsConnector()

    # Validate a configuration
    is_valid, message = connector.validate_config("pipeline.yaml")

    # Run a dry-run to see what would change
    result = connector.dry_run("pipeline.yaml")
    print(f"Would sync {result.secrets_processed} secrets")

    # Execute the full pipeline
    result = connector.run_pipeline("pipeline.yaml")
    if result.success:
        print(f"Synced {result.secrets_added} secrets")
"""

from __future__ import annotations

import json
import shutil
import subprocess

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from extended_data.connectors.base import VendorConnectorBase
from extended_data.logging import Logging


# Try to import native bindings
_NATIVE_AVAILABLE = False
try:
    import secretssync as _native

    _NATIVE_AVAILABLE = True
except ImportError:
    _native = None


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
    def from_native(cls, native_result: Any) -> SyncResult:
        """Create from native gopy result."""
        return cls(
            success=native_result.Success,
            target_count=native_result.TargetCount,
            secrets_processed=native_result.SecretsProcessed,
            secrets_added=native_result.SecretsAdded,
            secrets_modified=native_result.SecretsModified,
            secrets_removed=native_result.SecretsRemoved,
            secrets_unchanged=native_result.SecretsUnchanged,
            duration_ms=native_result.DurationMs,
            error_message=native_result.ErrorMessage,
            results_json=native_result.ResultsJSON,
            diff_output=native_result.DiffOutput,
        )

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

    @classmethod
    def from_native(cls, native_info: Any) -> ConfigInfo:
        """Create from native gopy result."""
        return cls(
            valid=native_info.Valid,
            error_message=native_info.ErrorMessage,
            source_count=native_info.SourceCount,
            target_count=native_info.TargetCount,
            sources=list(native_info.Sources) if native_info.Sources else [],
            targets=list(native_info.Targets) if native_info.Targets else [],
            has_merge_store=native_info.HasMergeStore,
            vault_address=native_info.VaultAddress,
            aws_region=native_info.AWSRegion,
        )


class SecretsConnector(VendorConnectorBase):
    """Enterprise-grade secret synchronization connector.

    This connector wraps the secretssync Go library, providing Python
    bindings for enterprise-grade secret synchronization between
    HashiCorp Vault and AWS Secrets Manager.

    Features:
    - Two-phase pipeline architecture (merge → sync)
    - Secret inheritance and deep merging
    - AWS Organizations discovery
    - Dry-run with visual diff output
    - CI/CD integration with exit codes

    The connector operates in two modes:
    1. Native mode: Uses gopy-generated bindings (faster)
    2. CLI mode: Falls back to subprocess if bindings unavailable
    """

    def __init__(
        self,
        cli_path: str | None = None,
        prefer_native: bool = True,
        logger: Logging | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the secrets connector.

        Args:
            cli_path: Path to secretsync CLI binary (for CLI mode)
            prefer_native: Prefer native bindings over CLI
            logger: Logger instance
            **kwargs: Passed to VendorConnectorBase
        """
        super().__init__(logger=logger, **kwargs)

        self._prefer_native = prefer_native and _NATIVE_AVAILABLE
        self._cli_path = cli_path or self._find_cli()

        mode = "native" if self._prefer_native else "CLI"
        self.logger.info(f"SecretsConnector initialized in {mode} mode")

    def _find_cli(self) -> str | None:
        """Find the secretsync CLI binary."""
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
    def native_available(self) -> bool:
        """Check if native bindings are available."""
        return _NATIVE_AVAILABLE

    @property
    def cli_available(self) -> bool:
        """Check if CLI is available."""
        return self._cli_path is not None

    def validate_config(self, config_path: str) -> tuple[bool, str]:
        """Validate a pipeline configuration file.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            Tuple of (is_valid, message)
        """
        if self._prefer_native:
            return _native.ValidateConfig(config_path)

        return self._cli_validate_config(config_path)

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

    def get_config_info(self, config_path: str) -> ConfigInfo:
        """Get detailed information about a configuration.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            ConfigInfo with configuration details
        """
        if self._prefer_native:
            native_info = _native.GetConfigInfo(config_path)
            return ConfigInfo.from_native(native_info)

        return self._cli_get_config_info(config_path)

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
    ) -> SyncResult:
        """Execute the secrets synchronization pipeline.

        Args:
            config_path: Path to YAML configuration file
            options: Execution options (defaults to full pipeline)

        Returns:
            SyncResult with operation details
        """
        options = options or SyncOptions()

        if self._prefer_native:
            return self._native_run_pipeline(config_path, options)

        return self._cli_run_pipeline(config_path, options)

    def _native_run_pipeline(
        self,
        config_path: str,
        options: SyncOptions,
    ) -> SyncResult:
        """Run pipeline via native bindings."""
        native_opts = _native.DefaultSyncOptions()
        native_opts.DryRun = options.dry_run
        native_opts.Operation = options.operation.value
        native_opts.Targets = ",".join(options.targets)
        native_opts.ContinueOnError = options.continue_on_error
        native_opts.Parallelism = options.parallelism
        native_opts.ComputeDiff = options.compute_diff
        native_opts.OutputFormat = options.output_format.value

        native_result = _native.RunPipeline(config_path, native_opts)
        return SyncResult.from_native(native_result)

    def _cli_run_pipeline(
        self,
        config_path: str,
        options: SyncOptions,
    ) -> SyncResult:
        """Run pipeline via CLI."""
        if not self._cli_path:
            return SyncResult(
                success=False,
                error_message="CLI not available and native bindings not installed",
            )

        # CLI mode always requests JSON so this Python surface can reliably
        # return a structured SyncResult. Native mode can pass through other
        # output formats because it returns a typed result directly.
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

            if result.returncode == 0:
                output = json.loads(result.stdout)
                if not isinstance(output, dict) or "success" not in output:
                    return SyncResult(
                        success=False,
                        error_message=(
                            "Unsupported secretsync JSON output: expected pipeline result envelope. "
                            "Upgrade secretsync or use native bindings."
                        ),
                    )
                return SyncResult.from_cli_output(output)
            else:
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

    def dry_run(self, config_path: str) -> SyncResult:
        """Perform a dry run of the pipeline.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            SyncResult with what would be changed
        """
        if self._prefer_native:
            native_result = _native.DryRun(config_path)
            return SyncResult.from_native(native_result)

        options = SyncOptions(dry_run=True, compute_diff=True)
        return self._cli_run_pipeline(config_path, options)

    def merge(self, config_path: str, dry_run: bool = False) -> SyncResult:
        """Run only the merge phase of the pipeline.

        Args:
            config_path: Path to YAML configuration file
            dry_run: If True, don't make actual changes

        Returns:
            SyncResult with merge operation details
        """
        if self._prefer_native:
            native_result = _native.Merge(config_path, dry_run)
            return SyncResult.from_native(native_result)

        options = SyncOptions(
            operation=SyncOperation.MERGE,
            dry_run=dry_run,
            compute_diff=dry_run,
        )
        return self._cli_run_pipeline(config_path, options)

    def sync(self, config_path: str, dry_run: bool = False) -> SyncResult:
        """Run only the sync phase of the pipeline.

        Args:
            config_path: Path to YAML configuration file
            dry_run: If True, don't make actual changes

        Returns:
            SyncResult with sync operation details
        """
        if self._prefer_native:
            native_result = _native.Sync(config_path, dry_run)
            return SyncResult.from_native(native_result)

        options = SyncOptions(
            operation=SyncOperation.SYNC,
            dry_run=dry_run,
            compute_diff=dry_run,
        )
        return self._cli_run_pipeline(config_path, options)

    def get_targets(self, config_path: str) -> tuple[list[str], str]:
        """Get the list of targets from a configuration.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            Tuple of (targets, error_message)
        """
        if self._prefer_native:
            targets, err = _native.GetTargets(config_path)
            return list(targets) if targets else [], err

        info = self.get_config_info(config_path)
        return info.targets, info.error_message

    def get_sources(self, config_path: str) -> tuple[list[str], str]:
        """Get the list of sources from a configuration.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            Tuple of (sources, error_message)
        """
        if self._prefer_native:
            sources, err = _native.GetSources(config_path)
            return list(sources) if sources else [], err

        info = self.get_config_info(config_path)
        return info.sources, info.error_message


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
