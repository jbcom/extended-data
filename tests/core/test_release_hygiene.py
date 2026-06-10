"""Release hygiene checks for repository automation."""

from __future__ import annotations

import re

from importlib import resources
from pathlib import Path

import tomlkit


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
OLD_PACKAGE_NAMESPACES = (
    "directed_inputs_class",
    "extended_data_types",
    "lifecyclelogging",
    "vendor_connectors",
)
REMOVED_PUBLIC_KEYWORDS = ("unhump_results",)
SECRETSSYNC_PROJECT_PATTERNS = (
    re.compile(r"\bsecretssync\s+(?:Go\s+)?(?:project|library|repo|repository|CLI|connector|bindings?)\b", re.IGNORECASE),
    re.compile(r"\b(?:project|library|repo|repository|CLI|connector|bindings?)\s+secretssync\b", re.IGNORECASE),
)


def _pyproject() -> tomlkit.TOMLDocument:
    return tomlkit.parse((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


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


def test_old_package_namespace_shims_do_not_exist() -> None:
    """Clean major-version breaks should not grow old import namespace shims."""
    offenders: list[str] = []

    for namespace in OLD_PACKAGE_NAMESPACES:
        package_path = REPO_ROOT / "src" / namespace
        module_path = REPO_ROOT / "src" / f"{namespace}.py"
        if package_path.exists():
            offenders.append(str(package_path.relative_to(REPO_ROOT)))
        if module_path.exists():
            offenders.append(str(module_path.relative_to(REPO_ROOT)))

    assert offenders == []


def test_typed_classifier_has_pep561_marker() -> None:
    """The typed package classifier should be backed by a PEP 561 marker."""
    classifiers = _pyproject()["project"]["classifiers"]

    assert "Typing :: Typed" in classifiers
    assert (REPO_ROOT / "src" / "extended_data" / "py.typed").is_file()
    assert resources.files("extended_data").joinpath("py.typed").is_file()


def test_public_guidance_does_not_use_removed_runtime_keywords() -> None:
    """Docs and examples should not keep teaching removed compatibility keywords."""
    offenders: list[str] = []
    paths = [REPO_ROOT / "README.md"]
    paths.extend(path for root in (REPO_ROOT / "docs", REPO_ROOT / "examples") for path in root.rglob("*"))

    for path in sorted(path for path in paths if path.is_file()):
        if path.suffix in {".pyc", ".png"}:
            continue
        text = path.read_text(encoding="utf-8")
        for keyword in REMOVED_PUBLIC_KEYWORDS:
            if keyword in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {keyword}")

    assert offenders == []


def test_public_guidance_names_secrets_sync_roles_precisely() -> None:
    """Use SecretSync for the product and reserve exact names for CLI/native modules."""
    offenders: list[str] = []
    paths = [REPO_ROOT / "README.md"]
    paths.extend(path for root in (REPO_ROOT / "docs", REPO_ROOT / "src") for path in root.rglob("*"))

    for path in sorted(path for path in paths if path.is_file()):
        if path.suffix in {".pyc", ".png"}:
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in SECRETSSYNC_PROJECT_PATTERNS:
            if pattern.search(text):
                offenders.append(str(path.relative_to(REPO_ROOT)))
                break

    assert offenders == []
