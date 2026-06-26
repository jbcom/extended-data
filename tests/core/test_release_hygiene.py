"""Release hygiene checks for repository automation."""

from __future__ import annotations

import re

from importlib import import_module, resources
from pathlib import Path

import tomlkit


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPO_ROOT / ".github" / "workflows"
ACTION_REF_WITH_COMMENT_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*([^#\s]+)(?:\s+#\s*(\S+))?")
PINNED_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ACTION_VERSION_COMMENT_RE = re.compile(r"^v\d+\.\d+\.\d+$")
PIN_TABLE_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*`([0-9a-f]{40})`\s*\|$")
PUBLIC_TEXT_ROOTS = (
    REPO_ROOT / "src",
    REPO_ROOT / "docs",
    REPO_ROOT / "examples",
    REPO_ROOT / "README.md",
)
GENERATED_PUBLIC_TEXT_ROOTS = (
    REPO_ROOT / "docs" / "_build",
    REPO_ROOT / "docs" / "apidocs",
)
PUBLIC_TEXT_IGNORED_SUFFIXES = {".pyc", ".png"}
OLD_PROJECT_TERMS = ("extended-data-library", "terraform-modules", "TerraformDataSource")
OLD_PUBLIC_API_NAMES = ("VendorConnectorBase",)
OLD_PACKAGE_NAMESPACES = (
    "directed_inputs_class",
    "extended_data_types",
    "lifecyclelogging",
    "vendor_connectors",
)
REMOVED_PUBLIC_KEYWORDS = ("prefer_native", "unhump_results")
FUTURE_API_PROMISES = ("will be available", "coming soon")
BOOTSTRAP_TEXT_MARKERS = ("(NEW)",)
EXTRACTION_ERA_FRAMING = (
    "remaining migration work",
    "unfinished migration work",
)
IMPRECISE_VENDOR_FRAMING = (
    "vendor data connectors",
    "vendor workflows",
    "vendor integrations",
    "vendor-specific",
    "vendor data payloads",
    "vendor data operations",
    "vendor payload handles",
    "vendor resource",
    "structured vendor payloads",
    "vendor or AI layers",
)
SECRETSSYNC_PROJECT_PATTERNS = (
    re.compile(r"\bsecretssync\s+(?:Go\s+)?(?:project|library|repo|repository|CLI|connector|bindings?)\b", re.IGNORECASE),
    re.compile(r"\b(?:project|library|repo|repository|CLI|connector|bindings?)\s+secretssync\b", re.IGNORECASE),
)
IMPRECISE_SECRETSSYNC_TERMS = ("secret sync primitives",)
EXTRA_REFERENCE_RE = re.compile(r"extended-data\[([^\]\n]+)\]")
NON_RUNTIME_EXTRAS = {"all", "dev", "docs", "tests", "typing"}
PACKAGE_SHAPE_RE = re.compile(r"^  ([a-z_]+)/\s+")
UNPATCHED_RUNTIME_VULNERABILITIES = {
    "chromadb": "GHSA-f4j7-r4q5-qw2c",
    "torch": "GHSA-rrmf-rvhw-rf47",
}


def _pyproject() -> tomlkit.TOMLDocument:
    return tomlkit.parse((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _uv_lock() -> tomlkit.TOMLDocument:
    return tomlkit.parse((REPO_ROOT / "uv.lock").read_text(encoding="utf-8"))


def _is_generated_public_text_path(path: Path) -> bool:
    for generated_root in GENERATED_PUBLIC_TEXT_ROOTS:
        try:
            path.relative_to(generated_root)
        except ValueError:
            continue
        return True
    return False


def _is_public_text_file(path: Path) -> bool:
    return path.is_file() and path.suffix not in PUBLIC_TEXT_IGNORED_SUFFIXES and not _is_generated_public_text_path(path)


def _iter_public_text_files(*roots: Path) -> list[Path]:
    paths: list[Path] = []
    for root in roots:
        if root.is_file():
            paths.append(root)
        else:
            paths.extend(path for path in root.rglob("*") if _is_public_text_file(path))
    return sorted(path for path in paths if _is_public_text_file(path))


def _requirement_name(requirement: str) -> str:
    name_chars: list[str] = []
    for char in requirement:
        if char.isalnum() or char in {"-", "_", "."}:
            name_chars.append(char)
            continue
        break
    return "".join(name_chars).lower().replace("_", "-")


def _workflow_action_pins() -> dict[str, tuple[str, str]]:
    pins: dict[str, tuple[str, str]] = {}
    offenders: list[str] = []

    for path in sorted(WORKFLOW_ROOT.glob("*.yml")) + sorted(WORKFLOW_ROOT.glob("*.yaml")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            match = ACTION_REF_WITH_COMMENT_RE.match(line)
            if match is None:
                continue

            uses = match.group(1).strip()
            if uses.startswith(("./", "docker://")):
                continue

            action, separator, ref = uses.rpartition("@")
            version = match.group(2)
            if not separator or PINNED_SHA_RE.fullmatch(ref) is None:
                relative_path = path.relative_to(REPO_ROOT)
                offenders.append(f"{relative_path}:{line_number}: {uses}")
                continue
            if version is None or ACTION_VERSION_COMMENT_RE.fullmatch(version) is None:
                relative_path = path.relative_to(REPO_ROOT)
                offenders.append(f"{relative_path}:{line_number}: missing stable version comment for {uses}")
                continue

            existing = pins.setdefault(action, (version, ref))
            if existing != (version, ref):
                relative_path = path.relative_to(REPO_ROOT)
                offenders.append(f"{relative_path}:{line_number}: conflicting pin for {action}")

    assert offenders == []
    return pins


def _publishing_checklist_pins() -> dict[str, tuple[str, str]]:
    pins: dict[str, tuple[str, str]] = {}
    checklist = (REPO_ROOT / "docs" / "PUBLISHING_CHECKLIST.md").read_text(encoding="utf-8")

    for line in checklist.splitlines():
        match = PIN_TABLE_RE.match(line.strip())
        if match is None:
            continue
        action, version, ref = match.groups()
        pins[action] = (version, ref)

    assert pins, "docs/PUBLISHING_CHECKLIST.md must list current workflow action pins"
    return pins


def test_workflow_actions_are_pinned_to_exact_shas() -> None:
    """Remote workflow actions should use immutable action commit SHAs."""
    assert _workflow_action_pins()


def test_publishing_checklist_matches_workflow_action_pins() -> None:
    """The release checklist should document the exact workflow action pins."""
    assert _publishing_checklist_pins() == _workflow_action_pins()


def test_release_workflow_uses_pypi_trusted_publishing() -> None:
    """Publishing should use PyPI trusted publishing instead of repository tokens."""
    release_workflow = (WORKFLOW_ROOT / "release.yml").read_text(encoding="utf-8")
    forbidden_token_markers = (
        "PYPI_API_TOKEN",
        "PYPI_TOKEN",
        "pypi-token",
        "pypi_token",
        "__token__",
        "secrets.PYPI",
    )

    assert "id-token: write" in release_workflow
    assert "uv publish --trusted-publishing always" in release_workflow
    assert "uv publish" in release_workflow
    assert all(marker not in release_workflow for marker in forbidden_token_markers)


def test_public_text_does_not_reference_old_project_origins() -> None:
    """Public code/docs should describe current Extended Data surfaces, not origin packages."""
    offenders: list[str] = []

    for path in _iter_public_text_files(*PUBLIC_TEXT_ROOTS):
        text = path.read_text(encoding="utf-8")
        for term in (*OLD_PROJECT_TERMS, *OLD_PUBLIC_API_NAMES):
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


def test_all_extra_contains_every_runtime_extra_dependency() -> None:
    """The broad install target should be the union of runtime feature extras."""
    extras = _pyproject()["project"]["optional-dependencies"]
    all_dependencies = {str(dependency) for dependency in extras["all"]}
    missing: list[str] = []

    for extra_name, dependencies in extras.items():
        if extra_name in NON_RUNTIME_EXTRAS:
            continue

        for dependency in dependencies:
            dependency_text = str(dependency)
            if dependency_text not in all_dependencies:
                missing.append(f"{extra_name}: {dependency_text}")

    assert missing == []


def test_dependency_manifests_do_not_lock_unpatched_runtime_vulnerabilities() -> None:
    """Runtime dependency manifests should not carry known unpatched vulnerable packages."""
    vulnerable = set(UNPATCHED_RUNTIME_VULNERABILITIES)
    offenders: list[str] = []
    project = _pyproject()["project"]

    for dependency in project["dependencies"]:
        name = _requirement_name(str(dependency))
        if name in vulnerable:
            offenders.append(f"pyproject.toml dependency {dependency}: {UNPATCHED_RUNTIME_VULNERABILITIES[name]}")

    for extra_name, dependencies in project["optional-dependencies"].items():
        for dependency in dependencies:
            name = _requirement_name(str(dependency))
            if name in vulnerable:
                offenders.append(f"pyproject.toml extra {extra_name} dependency {dependency}: {UNPATCHED_RUNTIME_VULNERABILITIES[name]}")

    for package in _uv_lock()["package"]:
        name = str(package["name"]).lower().replace("_", "-")
        if name in vulnerable:
            offenders.append(f"uv.lock package {name}: {UNPATCHED_RUNTIME_VULNERABILITIES[name]}")

    assert offenders == []


def test_public_install_guidance_names_known_extras() -> None:
    """Static install examples should not teach extras that pyproject does not publish."""
    known_extras = set(_pyproject()["project"]["optional-dependencies"])
    offenders: list[str] = []
    for path in _iter_public_text_files(REPO_ROOT / "README.md", REPO_ROOT / "docs", REPO_ROOT / "examples", REPO_ROOT / "src"):
        relative_path = path.relative_to(REPO_ROOT)
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for match in EXTRA_REFERENCE_RE.finditer(line):
                extra_group = match.group(1)
                if "..." in extra_group or "{" in extra_group or "}" in extra_group:
                    continue

                for extra in (part.strip() for part in extra_group.split(",")):
                    if extra and extra not in known_extras:
                        offenders.append(f"{relative_path}:{line_number}: {extra} in extended-data[{extra_group}]")

    assert offenders == []


def test_public_install_guidance_documents_every_runtime_extra() -> None:
    """Every runtime optional extra should be discoverable from public install guidance."""
    runtime_extras = set(_pyproject()["project"]["optional-dependencies"]) - NON_RUNTIME_EXTRAS
    documented_extras: set[str] = set()
    text = "\n".join(
        [
            (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
            (REPO_ROOT / "docs" / "package-surface.md").read_text(encoding="utf-8"),
        ],
    )

    for match in EXTRA_REFERENCE_RE.finditer(text):
        extra_group = match.group(1)
        if "..." in extra_group or "{" in extra_group or "}" in extra_group:
            continue
        documented_extras.update(extra.strip() for extra in extra_group.split(",") if extra.strip())

    assert runtime_extras <= documented_extras


def test_project_scripts_point_to_callables() -> None:
    """Console-script metadata should resolve to importable callables."""
    scripts = _pyproject()["project"]["scripts"]
    offenders: list[str] = []

    for script_name, target in scripts.items():
        module_name, separator, attribute_name = str(target).partition(":")
        if not separator:
            offenders.append(f"{script_name}: {target} has no attribute separator")
            continue

        try:
            module = import_module(module_name)
        except Exception as exc:
            offenders.append(f"{script_name}: cannot import {module_name}: {exc}")
            continue

        entry_point = getattr(module, attribute_name, None)
        if not callable(entry_point):
            offenders.append(f"{script_name}: {target} is not callable")

    assert offenders == []


def test_project_scripts_preserve_package_cli_boundaries() -> None:
    """The broad CLI entrypoint should not regress to a connector-only module."""
    scripts = {str(name): str(target) for name, target in _pyproject()["project"]["scripts"].items()}

    assert scripts == {
        "extended-data": "extended_data.cli:main",
        "extended-data-mcp": "extended_data.connectors.mcp:main",
        "meshy-mcp": "extended_data.connectors.meshy.mcp:main",
    }


def test_readme_package_shape_matches_public_subpackages() -> None:
    """The documented tier layout should match the actual top-level package directories."""
    source_root = REPO_ROOT / "src" / "extended_data"
    actual_subpackages = {
        path.name
        for path in source_root.iterdir()
        if path.is_dir() and not path.name.startswith("__") and (path / "__init__.py").is_file()
    }
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    try:
        package_shape = readme.split("## Package Shape", 1)[1].split("```", 2)[1]
    except IndexError as exc:
        raise AssertionError("README.md must document the package shape in a fenced block") from exc

    documented_subpackages = {
        match.group(1) for line in package_shape.splitlines() if (match := PACKAGE_SHAPE_RE.match(line))
    }

    assert documented_subpackages == actual_subpackages


def test_public_guidance_does_not_use_removed_runtime_keywords() -> None:
    """Docs and examples should not keep teaching removed compatibility keywords."""
    offenders: list[str] = []
    for path in _iter_public_text_files(REPO_ROOT / "README.md", REPO_ROOT / "docs", REPO_ROOT / "examples"):
        text = path.read_text(encoding="utf-8")
        for keyword in REMOVED_PUBLIC_KEYWORDS:
            if keyword in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {keyword}")

    assert offenders == []


def test_public_guidance_uses_integrated_connector_framing() -> None:
    """Public docs should frame connectors as integrated external-data surfaces."""
    offenders: list[str] = []
    for path in _iter_public_text_files(REPO_ROOT / "README.md", REPO_ROOT / "docs", REPO_ROOT / "examples", REPO_ROOT / "src"):
        text = path.read_text(encoding="utf-8")
        for phrase in IMPRECISE_VENDOR_FRAMING:
            if phrase in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {phrase}")

    assert offenders == []


def test_public_guidance_uses_standalone_package_framing() -> None:
    """Public docs should not frame Extended Data as an extraction artifact."""
    offenders: list[str] = []
    for path in _iter_public_text_files(REPO_ROOT / "README.md", REPO_ROOT / "docs", REPO_ROOT / "examples", REPO_ROOT / "src"):
        text = path.read_text(encoding="utf-8")
        for phrase in EXTRACTION_ERA_FRAMING:
            if phrase in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {phrase}")

    assert offenders == []


def test_public_text_does_not_promise_future_api_surfaces() -> None:
    """Clean-break docs should describe current surfaces instead of placeholders."""
    offenders: list[str] = []
    for path in _iter_public_text_files(REPO_ROOT / "README.md", REPO_ROOT / "docs", REPO_ROOT / "examples", REPO_ROOT / "src"):
        relative_path = path.relative_to(REPO_ROOT)
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            normalized = line.lower()
            for phrase in FUTURE_API_PROMISES:
                if phrase in normalized:
                    offenders.append(f"{relative_path}:{line_number}: {phrase}")

    assert offenders == []


def test_public_text_does_not_keep_bootstrap_markers() -> None:
    """Extracted package docs should not keep launch-era status markers."""
    offenders: list[str] = []
    for path in _iter_public_text_files(REPO_ROOT / "README.md", REPO_ROOT / "docs", REPO_ROOT / "examples", REPO_ROOT / "src"):
        relative_path = path.relative_to(REPO_ROOT)
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for marker in BOOTSTRAP_TEXT_MARKERS:
                if marker in line:
                    offenders.append(f"{relative_path}:{line_number}: {marker}")

    assert offenders == []


def test_public_guidance_names_secrets_sync_roles_precisely() -> None:
    """Use SecretSync for the product and reserve exact names for CLI modules."""
    offenders: list[str] = []
    for path in _iter_public_text_files(REPO_ROOT / "README.md", REPO_ROOT / "docs", REPO_ROOT / "src"):
        text = path.read_text(encoding="utf-8")
        for pattern in SECRETSSYNC_PROJECT_PATTERNS:
            if pattern.search(text):
                offenders.append(str(path.relative_to(REPO_ROOT)))
                break
        for term in IMPRECISE_SECRETSSYNC_TERMS:
            if term in text.lower():
                offenders.append(f"{path.relative_to(REPO_ROOT)}: {term}")

    assert offenders == []
