"""Release hygiene checks for repository automation."""

from __future__ import annotations

import re

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPO_ROOT / ".github" / "workflows"
ACTION_REF_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*([^#\s]+)")
PINNED_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
PUBLIC_TEXT_ROOTS = (
    REPO_ROOT / "src",
    REPO_ROOT / "docs",
    REPO_ROOT / "examples",
    REPO_ROOT / "README.md",
)
OLD_PROJECT_TERMS = ("terraform-modules", "TerraformDataSource")


def test_workflow_actions_are_pinned_to_exact_shas() -> None:
    """Remote workflow actions should use immutable action commit SHAs."""
    offenders: list[str] = []

    for path in sorted(WORKFLOW_ROOT.glob("*.yml")) + sorted(WORKFLOW_ROOT.glob("*.yaml")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            match = ACTION_REF_RE.match(line)
            if match is None:
                continue

            uses = match.group(1).strip()
            if uses.startswith(("./", "docker://")):
                continue

            _, separator, ref = uses.rpartition("@")
            if not separator or PINNED_SHA_RE.fullmatch(ref) is None:
                relative_path = path.relative_to(REPO_ROOT)
                offenders.append(f"{relative_path}:{line_number}: {uses}")

    assert offenders == []


def test_public_text_does_not_reference_old_project_origins() -> None:
    """Public code/docs should describe current Extended Data surfaces, not origin packages."""
    offenders: list[str] = []

    paths: list[Path] = []
    for root in PUBLIC_TEXT_ROOTS:
        if root.is_file():
            paths.append(root)
        else:
            paths.extend(path for path in root.rglob("*") if path.is_file())

    for path in sorted(paths):
        if path.suffix in {".pyc", ".png"}:
            continue
        text = path.read_text(encoding="utf-8")
        for term in OLD_PROJECT_TERMS:
            if term in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {term}")

    assert offenders == []
