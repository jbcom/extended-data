"""Smoke tests for examples that do not require live vendor credentials."""

from __future__ import annotations

import importlib.util
import os
import py_compile
import subprocess
import sys

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SAFE_EXAMPLES = [
    "examples/core/basic_usage.py",
    "examples/core/composed_workflows.py",
    "examples/core/file_operations.py",
    "examples/core/serialization.py",
    "examples/core/string_transformations.py",
    "examples/inputs/basic_usage.py",
    "examples/inputs/decorator_api.py",
    "examples/inputs/encoding_decoding.py",
    "examples/logging/basic_logging.py",
    "examples/logging/exit_run_formatting.py",
    "examples/logging/markers_and_storage.py",
    "examples/logging/verbosity_control.py",
]
CONNECTOR_EXAMPLES = [
    "examples/connectors/basic_aws.py",
    "examples/connectors/basic_google.py",
    "examples/connectors/basic_meshy.py",
    "examples/connectors/langchain_tools.py",
    "examples/connectors/mcp_server.py",
]
ALL_EXAMPLES = SAFE_EXAMPLES + CONNECTOR_EXAMPLES


@pytest.mark.parametrize("example_path", SAFE_EXAMPLES)
def test_safe_example_runs(example_path: str, tmp_path: Path) -> None:
    """Keep runnable examples aligned with the installed package surface."""
    env = os.environ.copy()
    env.pop("OVERRIDE_STDIN", None)

    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / example_path)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert result.returncode == 0, f"{example_path} failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"


@pytest.mark.parametrize("example_path", ALL_EXAMPLES)
def test_example_compiles(example_path: str, tmp_path: Path) -> None:
    """Every example should at least remain syntactically valid."""
    py_compile.compile(str(REPO_ROOT / example_path), cfile=str(tmp_path / "example.pyc"), doraise=True)


@pytest.mark.parametrize("example_path", CONNECTOR_EXAMPLES)
def test_connector_example_imports_without_live_credentials(example_path: str) -> None:
    """Credential-gated connector examples should keep import-time side effects out."""
    module_path = REPO_ROOT / example_path
    module_name = example_path.replace("/", "_").removesuffix(".py")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    assert callable(module.main)
