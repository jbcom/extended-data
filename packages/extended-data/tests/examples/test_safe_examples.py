"""Smoke tests for runnable extended-data examples."""

from __future__ import annotations

import ast
import os
import py_compile
import re
import subprocess
import sys
import textwrap

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
PYTHON_MARKDOWN_BLOCK_RE = re.compile(r"```python\n(?P<code>.*?)\n```", re.DOTALL)
EXAMPLE_LITERAL_INCLUDE_RE = re.compile(r"^\.\. literalinclude::\s+\.\./\.\./(?P<path>examples/[^\s]+\.py)", re.MULTILINE)
SENSITIVE_IDENTIFIER_RE = re.compile(r"(api_?key|secret|token|password|authorization)", re.IGNORECASE)


def _readme_usage_snippet() -> str:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    usage_section = readme.split("## Usage", 1)[1].split("## Package Shape", 1)[0]
    match = re.search(r"```python\n(?P<code>.*?)\n```", usage_section, re.DOTALL)
    assert match is not None
    return match.group("code")


def _rst_python_code_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    lines = text.splitlines()
    index = 0

    while index < len(lines):
        if lines[index].strip() not in {".. code:: python", ".. code-block:: python"}:
            index += 1
            continue

        index += 1
        while index < len(lines) and (not lines[index].strip() or lines[index].startswith("   :")):
            index += 1

        block: list[str] = []
        while index < len(lines):
            line = lines[index]
            if not line.strip():
                block.append(line)
                index += 1
                continue
            if not line.startswith(("   ", "\t")):
                break
            block.append(line)
            index += 1

        if block:
            blocks.append(textwrap.dedent("\n".join(block)).strip())

    return blocks


def test_example_inventory_is_complete() -> None:
    """Every Python example should be explicitly classified for test coverage."""
    discovered = sorted(
        str(path.relative_to(REPO_ROOT))
        for path in (REPO_ROOT / "examples").rglob("*.py")
        if path.name != "__init__.py"
    )

    assert sorted(ALL_EXAMPLES) == discovered


def test_all_examples_are_included_in_sphinx_docs() -> None:
    """Every runnable example should be rendered from source in Sphinx docs."""
    documented: set[str] = set()

    for path in sorted((REPO_ROOT / "docs" / "examples").glob("*.rst")):
        text = path.read_text(encoding="utf-8")
        documented.update(match.group("path") for match in EXAMPLE_LITERAL_INCLUDE_RE.finditer(text))

    assert set(ALL_EXAMPLES) == documented


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


def test_documentation_python_snippets_compile() -> None:
    """Documentation snippets may be conceptual, but they should remain valid Python."""
    markdown_paths = [REPO_ROOT / "README.md"]
    rst_paths = sorted((REPO_ROOT / "docs").rglob("*.rst"))
    offenders: list[str] = []

    for path in sorted(markdown_paths):
        text = path.read_text(encoding="utf-8")
        for index, match in enumerate(PYTHON_MARKDOWN_BLOCK_RE.finditer(text), start=1):
            code = match.group("code")
            try:
                compile(code, f"{path.relative_to(REPO_ROOT)}#python-block-{index}", "exec")
            except SyntaxError as exc:
                offenders.append(f"{path.relative_to(REPO_ROOT)} block {index}: {exc}")

    for path in rst_paths:
        text = path.read_text(encoding="utf-8")
        for index, code in enumerate(_rst_python_code_blocks(text), start=1):
            try:
                compile(code, f"{path.relative_to(REPO_ROOT)}#python-block-{index}", "exec")
            except SyntaxError as exc:
                offenders.append(f"{path.relative_to(REPO_ROOT)} block {index}: {exc}")

    assert offenders == []


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


def test_composed_workflow_example_uses_named_transforms() -> None:
    """The workflow example should exercise public merge and transform APIs."""
    text = (REPO_ROOT / "examples/core/composed_workflows.py").read_text(encoding="utf-8")

    assert ".merge(" in text
    assert ".transform(" in text
    assert "list_data_transform_steps" in text


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


def _is_sensitive_identifier(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return bool(SENSITIVE_IDENTIFIER_RE.search(node.id))
    if isinstance(node, ast.Attribute):
        return bool(SENSITIVE_IDENTIFIER_RE.search(node.attr))
    return False


def _expression_contains_sensitive_identifier(node: ast.AST) -> bool:
    return any(_is_sensitive_identifier(child) for child in ast.walk(node))


def test_examples_do_not_echo_partial_sensitive_values() -> None:
    """Examples should not teach printing, slicing, or returning credential fragments."""
    offenders: list[str] = []

    for example_path in ALL_EXAMPLES:
        tree = ast.parse((REPO_ROOT / example_path).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript) and _is_sensitive_identifier(node.value):
                offenders.append(f"{example_path}:{node.lineno}: slices or indexes a sensitive value")
            if isinstance(node, ast.FormattedValue) and _expression_contains_sensitive_identifier(node.value):
                offenders.append(f"{example_path}:{node.lineno}: interpolates a sensitive value")
            if isinstance(node, ast.Return) and node.value is not None and _is_sensitive_identifier(node.value):
                offenders.append(f"{example_path}:{node.lineno}: returns a sensitive value directly")

    assert offenders == []


@pytest.mark.parametrize("example_path", ALL_EXAMPLES)
def test_example_compiles(example_path: str, tmp_path: Path) -> None:
    """Every example should at least remain syntactically valid."""
    py_compile.compile(str(REPO_ROOT / example_path), cfile=str(tmp_path / "example.pyc"), doraise=True)
