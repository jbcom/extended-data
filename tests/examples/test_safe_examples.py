"""Smoke tests for examples that do not require live vendor credentials."""

from __future__ import annotations

import ast
import importlib.util
import os
import py_compile
import re
import subprocess
import sys

from pathlib import Path

import pytest

from extended_data import primitives


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
STALE_EXAMPLE_COMMANDS = (
    "python examples/mcp_server.py",
    "python -m examples.decorator_api",
    "python -m examples.encoding_decoding",
)
FUNCTION_FIRST_BASIC_USAGE_HELPERS = (
    "deep_merge",
    "filter_list",
    "filter_map",
    "flatten_list",
    "flatten_map",
    "sanitize_key",
    "truncate",
)
ROOT_DISALLOWED_TIER1_IMPORTS = tuple(sorted(primitives.__all__))


def _readme_usage_snippet() -> str:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    usage_section = readme.split("## Usage", 1)[1].split("## Package Shape", 1)[0]
    match = re.search(r"```python\n(?P<code>.*?)\n```", usage_section, re.DOTALL)
    assert match is not None
    return match.group("code")


def test_example_inventory_is_complete() -> None:
    """Every Python example should be explicitly classified for test coverage."""
    discovered = sorted(
        str(path.relative_to(REPO_ROOT))
        for path in (REPO_ROOT / "examples").rglob("*.py")
        if path.name != "__init__.py"
    )

    assert sorted(ALL_EXAMPLES) == discovered


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


def test_readme_usage_snippet_runs(tmp_path: Path) -> None:
    """Keep the primary README example executable as a public contract."""
    env = os.environ.copy()
    env.pop("OVERRIDE_STDIN", None)

    result = subprocess.run(
        [sys.executable, "-c", _readme_usage_snippet()],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert result.returncode == 0, f"README usage snippet failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"


def test_examples_do_not_document_stale_command_paths() -> None:
    """Example command snippets should point at the current directory layout."""
    offenders: list[str] = []

    for example_path in ALL_EXAMPLES:
        text = (REPO_ROOT / example_path).read_text(encoding="utf-8")
        for command in STALE_EXAMPLE_COMMANDS:
            if command in text:
                offenders.append(f"{example_path}: {command}")

    assert offenders == []


def test_basic_core_example_uses_container_first_operations() -> None:
    """The basic example should lead with Tier 2 methods for list/map/string workflows."""
    text = (REPO_ROOT / "examples/core/basic_usage.py").read_text(encoding="utf-8")
    import_block = text.split("from extended_data import (", maxsplit=1)[1].split(")", maxsplit=1)[0]

    offenders = [name for name in FUNCTION_FIRST_BASIC_USAGE_HELPERS if name in import_block]

    assert offenders == []


def test_examples_do_not_import_tier1_utilities_from_root() -> None:
    """Examples should import pure Tier 1 utilities from extended_data.primitives."""
    offenders: list[str] = []

    for example_path in ALL_EXAMPLES:
        text = (REPO_ROOT / example_path).read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or node.module != "extended_data":
                continue

            imported_names = {alias.name for alias in node.names}
            disallowed = sorted(imported_names.intersection(ROOT_DISALLOWED_TIER1_IMPORTS))
            if disallowed:
                offenders.append(f"{example_path}: {', '.join(disallowed)}")

    assert offenders == []


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
