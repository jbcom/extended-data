"""Smoke tests for examples that do not require live vendor credentials."""

from __future__ import annotations

import os
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
