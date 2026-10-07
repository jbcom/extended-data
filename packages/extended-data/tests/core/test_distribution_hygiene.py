"""Regression coverage for the native archive privacy gate."""

from __future__ import annotations

import io
import runpy
import subprocess
import sys
import tarfile
import zipfile

from pathlib import Path

import pytest


WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
VERIFIER = WORKSPACE_ROOT / "scripts" / "verify_distributions.py"


def _write_pair(directory: Path) -> tuple[Path, Path]:
    wheel = directory / "extended_data-1.0.0-py3-none-any.whl"
    sdist = directory / "extended_data-1.0.0.tar.gz"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("extended_data/__init__.py", "")
    with tarfile.open(sdist, "w:gz") as archive:
        for name in ("src/extended_data/__init__.py", "pyproject.toml", "README.md"):
            member = tarfile.TarInfo(f"extended_data-1.0.0/{name}")
            member.size = 0
            archive.addfile(member, io.BytesIO())
    return wheel, sdist


def test_distribution_gate_accepts_clean_pair(tmp_path: Path) -> None:
    _write_pair(tmp_path)
    result = subprocess.run([sys.executable, str(VERIFIER), str(tmp_path)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("name", ["docs/_build/cache.doctree", ".agent-state/queue.json", "src/example/.claude/settings.json"])
def test_distribution_gate_rejects_private_members(tmp_path: Path, name: str) -> None:
    wheel, _ = _write_pair(tmp_path)
    with zipfile.ZipFile(wheel, "a") as archive:
        archive.writestr(name, "local state")
    result = subprocess.run([sys.executable, str(VERIFIER), str(tmp_path)], capture_output=True, text=True, check=False)
    assert result.returncode == 1
    assert f"forbidden member {name}" in result.stdout


@pytest.mark.parametrize("machine_path", [
    f"/{'Users'}/example/project/file.py",
    "/home/example/project/file.py",
    "/root/project/file.py",
    r"C:\Users\example\project\file.py",
    "C:/Users/example/project/file.py",
])
def test_distribution_gate_rejects_machine_paths_in_sdist(tmp_path: Path, machine_path: str) -> None:
    _, sdist = _write_pair(tmp_path)
    with tarfile.open(sdist, "r:gz") as archive:
        contents = [(member, archive.extractfile(member).read()) for member in archive.getmembers()]
    with tarfile.open(sdist, "w:gz") as archive:
        for member, data in contents:
            archive.addfile(member, io.BytesIO(data))
        data = machine_path.encode()
        member = tarfile.TarInfo("extended_data-1.0.0/tests/cache.pickle")
        member.size = len(data)
        archive.addfile(member, io.BytesIO(data))
    result = subprocess.run([sys.executable, str(VERIFIER), str(tmp_path)], capture_output=True, text=True, check=False)
    assert result.returncode == 1
    assert "machine path in" in result.stdout


@pytest.mark.parametrize("placeholder", ["/home/<user>/project", r"C:\Users\<user>\project", "/root/<project>"])
def test_distribution_gate_allows_documentation_placeholders(tmp_path: Path, placeholder: str) -> None:
    wheel, _ = _write_pair(tmp_path)
    with zipfile.ZipFile(wheel, "a") as archive:
        archive.writestr("extended_data/example.txt", placeholder)
    verify_directory = runpy.run_path(str(VERIFIER))["verify_directory"]
    assert verify_directory(tmp_path) == []


def test_distribution_gate_rejects_missing_artifacts_and_source(tmp_path: Path) -> None:
    verify_directory = runpy.run_path(str(VERIFIER))["verify_directory"]
    assert len(verify_directory(tmp_path)) == 2
    wheel, _ = _write_pair(tmp_path)
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("README.md", "")
    assert any("missing extended_data/__init__.py" in error for error in verify_directory(tmp_path))
