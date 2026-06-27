"""Release hygiene checks for repository automation."""

from __future__ import annotations

import json
import re

from importlib import import_module, resources
from pathlib import Path

import tomlkit
import yaml


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
REPO_ROOT = PACKAGE_ROOT
WORKFLOW_ROOT = WORKSPACE_ROOT / ".github" / "workflows"
DEPENDABOT_CONFIG = WORKSPACE_ROOT / ".github" / "dependabot.yml"
AGENTIC_REINFORCEMENT = WORKSPACE_ROOT / "AGENTIC_REINFORCEMENT.md"
SECRETSSYNC_ALIGNMENT = WORKSPACE_ROOT / "SECRETS_SYNC_ALIGNMENT.md"
PYTEST_PLUGIN_ROOT = WORKSPACE_ROOT / "packages" / "pytest-extended-data"
ACTION_REF_WITH_COMMENT_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*([^#\s]+)(?:\s+#\s*(\S+))?")
PINNED_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ACTION_VERSION_COMMENT_RE = re.compile(r"^v\d+\.\d+\.\d+$")
PIN_TABLE_RE = re.compile(r"^\|\s*`{1,2}([^`]+)`{1,2}\s*\|\s*`{1,2}([^`]+)`{1,2}\s*\|\s*`{1,2}([0-9a-f]{40})`{1,2}\s*\|$")
PUBLIC_TEXT_ROOTS = (
    PACKAGE_ROOT / "src",
    PACKAGE_ROOT / "docs",
    PACKAGE_ROOT / "examples",
    PACKAGE_ROOT / "README.md",
)
GENERATED_PUBLIC_TEXT_ROOTS = (
    PACKAGE_ROOT / "docs" / "_build",
    PACKAGE_ROOT / "docs" / "apidocs",
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
BOUNDARY_DRIFT_TERMS = (
    "connector handoff",
    "``vendor-fabric`` owns agent workflows",
    "``vendor-fabric`` owns external API clients, optional provider SDK\n"
    "dependencies, MCP/tool adapters",
    "| SecretSync agent tool | ``jbcom/vendor-fabric``",
    "| Agent framework       | ``jbcom/vendor-fabric``",
)
REMOVED_IN_PACKAGE_SURFACES = (
    "ConnectorFabric",
    "SecretsConnector",
    "from extended_data.connectors",
    "from extended_data.secrets",
    "extended-data[aws",
    "extended-data[google",
    "extended-data[github",
    "extended-data[meshy",
    "extended-data[secrets",
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
    return tomlkit.parse((PACKAGE_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _workspace_pyproject() -> tomlkit.TOMLDocument:
    return tomlkit.parse((WORKSPACE_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _pytest_plugin_pyproject() -> tomlkit.TOMLDocument:
    return tomlkit.parse((PYTEST_PLUGIN_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _uv_lock() -> tomlkit.TOMLDocument:
    return tomlkit.parse((WORKSPACE_ROOT / "uv.lock").read_text(encoding="utf-8"))


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
                relative_path = path.relative_to(WORKSPACE_ROOT)
                offenders.append(f"{relative_path}:{line_number}: {uses}")
                continue
            if version is None or ACTION_VERSION_COMMENT_RE.fullmatch(version) is None:
                relative_path = path.relative_to(WORKSPACE_ROOT)
                offenders.append(f"{relative_path}:{line_number}: missing stable version comment for {uses}")
                continue

            existing = pins.setdefault(action, (version, ref))
            if existing != (version, ref):
                relative_path = path.relative_to(WORKSPACE_ROOT)
                offenders.append(f"{relative_path}:{line_number}: conflicting pin for {action}")

    assert offenders == []
    return pins


def _publishing_checklist_pins() -> dict[str, tuple[str, str]]:
    pins: dict[str, tuple[str, str]] = {}
    checklist = (PACKAGE_ROOT / "docs" / "PUBLISHING_CHECKLIST.rst").read_text(encoding="utf-8")

    for line in checklist.splitlines():
        match = PIN_TABLE_RE.match(line.strip())
        if match is None:
            continue
        action, version, ref = match.groups()
        pins[action] = (version, ref)

    assert pins, "packages/extended-data/docs/PUBLISHING_CHECKLIST.rst must list current workflow action pins"
    return pins


def test_workflow_actions_are_pinned_to_exact_shas() -> None:
    """Remote workflow actions should use immutable action commit SHAs."""
    assert _workflow_action_pins()


def test_publishing_checklist_matches_workflow_action_pins() -> None:
    """The release checklist should document the exact workflow action pins."""
    assert _publishing_checklist_pins() == _workflow_action_pins()


def test_cd_workflow_uses_pypi_trusted_publishing() -> None:
    """Publishing should use PyPI trusted publishing from the standard CD workflow."""
    cd_workflow = (WORKFLOW_ROOT / "cd.yml").read_text(encoding="utf-8")
    release_workflow = (WORKFLOW_ROOT / "release.yml").read_text(encoding="utf-8")
    forbidden_token_markers = (
        "PYPI_API_TOKEN",
        "PYPI_TOKEN",
        "pypi-token",
        "pypi_token",
        "__token__",
        "secrets.PYPI",
    )

    assert "id-token: write" in cd_workflow
    assert "uv publish --trusted-publishing always" in cd_workflow
    assert "uv publish" in cd_workflow
    assert "extended-data|pytest-extended-data" in cd_workflow
    assert 'uv build --package "${{ inputs.package }}"' in cd_workflow
    for marker in forbidden_token_markers:
        assert marker not in cd_workflow
    assert "uv publish" not in release_workflow
    assert not (WORKFLOW_ROOT / "cd-pytest-extended-data.yml").exists()


def test_release_workflow_dispatches_cd_after_release_please() -> None:
    """Release Please should own releases and hand successful release tags to CD."""
    release_workflow = (WORKFLOW_ROOT / "release.yml").read_text(encoding="utf-8")

    assert "googleapis/release-please-action@" in release_workflow
    assert "GH_REPO: ${{ github.repository }}" in release_workflow
    assert "packages/extended-data--release_created" in release_workflow
    assert "packages/pytest-extended-data--release_created" in release_workflow
    assert 'gh workflow run cd.yml --repo "$GH_REPO" --ref main -f tag="$RELEASE_TAG" -f package="extended-data"' in release_workflow
    assert 'gh workflow run cd.yml --repo "$GH_REPO" --ref main -f tag="$RELEASE_TAG" -f package="pytest-extended-data"' in release_workflow


def test_standard_workflow_file_set_is_present() -> None:
    """Repository automation should use the standard ci/release/cd/automerge names."""
    required_workflows = {"ci.yml", "release.yml", "cd.yml", "automerge.yml"}
    workflow_names = {path.name for path in WORKFLOW_ROOT.glob("*.yml")}

    assert required_workflows.issubset(workflow_names)
    for workflow_name in required_workflows:
        assert (WORKFLOW_ROOT / workflow_name).is_file()
    assert all(not name.startswith("cd-") for name in workflow_names)


def test_automerge_workflow_limits_default_token_permissions() -> None:
    """Automerge should use a minimal base-context token without checking out PR code."""
    automerge_workflow = (WORKFLOW_ROOT / "automerge.yml").read_text(encoding="utf-8")
    workflow = yaml.load(automerge_workflow, Loader=yaml.BaseLoader)
    automerge_steps = workflow["jobs"]["automerge"]["steps"]
    merge_step = next(step for step in automerge_steps if step["name"] == "Enable auto-merge (squash)")

    assert "pull_request_target" in workflow["on"]
    assert workflow["permissions"] == {"contents": "write", "pull-requests": "write"}
    assert merge_step["env"]["GH_TOKEN"] == "${{ github.token }}"
    for step in automerge_steps:
        assert step.get("uses") != "actions/checkout"


def test_dependabot_covers_workspace_package_directories() -> None:
    """Dependabot should check each uv workspace package, plus root workflow files."""
    dependabot = yaml.safe_load(DEPENDABOT_CONFIG.read_text(encoding="utf-8"))
    updates = dependabot["updates"]

    pip_directories = {
        update["directory"] for update in updates if update["package-ecosystem"] == "pip"
    }
    github_actions_directories = {
        update["directory"] for update in updates if update["package-ecosystem"] == "github-actions"
    }

    assert pip_directories == {"/", "/packages/extended-data", "/packages/pytest-extended-data"}
    assert github_actions_directories == {"/"}
    for update in updates:
        assert update["schedule"]["interval"] == "weekly"


def test_workspace_declares_runtime_and_pytest_plugin_packages() -> None:
    """The repository root should be an unpublished uv workspace."""
    workspace = _workspace_pyproject()

    assert workspace["tool"]["uv"]["package"] is False
    assert set(workspace["tool"]["uv"]["workspace"]["members"]) == {
        "packages/extended-data",
        "packages/pytest-extended-data",
    }
    assert workspace["tool"]["uv"]["sources"]["extended-data"]["workspace"] is True
    assert workspace["tool"]["uv"]["sources"]["pytest-extended-data"]["workspace"] is True


def test_release_please_tracks_workspace_package_paths() -> None:
    """Release Please should publish package paths instead of the workspace root."""
    config = json.loads((WORKSPACE_ROOT / "release-please-config.json").read_text(encoding="utf-8"))
    manifest = json.loads((WORKSPACE_ROOT / ".release-please-manifest.json").read_text(encoding="utf-8"))

    assert set(config["packages"]) == {"packages/extended-data", "packages/pytest-extended-data"}
    assert set(manifest) == {"packages/extended-data", "packages/pytest-extended-data"}
    assert config["packages"]["packages/extended-data"]["package-name"] == "extended-data"
    assert config["packages"]["packages/pytest-extended-data"]["package-name"] == "pytest-extended-data"
    for package_config in config["packages"].values():
        assert package_config["release-type"] == "python"
        assert "extra-files" not in package_config


def test_pytest_plugin_package_exposes_pytest11_entrypoint() -> None:
    """Shared pytest behavior should live in the plugin package, not runtime code."""
    plugin_project = _pytest_plugin_pyproject()["project"]

    assert plugin_project["name"] == "pytest-extended-data"
    assert "extended-data>=8.3.1" in plugin_project["dependencies"]
    assert plugin_project["entry-points"]["pytest11"]["extended_data"] == "pytest_extended_data.plugin"
    assert (PYTEST_PLUGIN_ROOT / "src" / "pytest_extended_data" / "py.typed").is_file()


def test_public_text_does_not_reference_old_project_origins() -> None:
    """Public code/docs should describe current Extended Data surfaces, not origin packages."""
    offenders: list[str] = []

    for path in _iter_public_text_files(*PUBLIC_TEXT_ROOTS):
        text = path.read_text(encoding="utf-8")
        for term in (*OLD_PROJECT_TERMS, *OLD_PUBLIC_API_NAMES):
            if term in text:
                offenders.append(f"{path.relative_to(PACKAGE_ROOT)}: {term}")

    assert offenders == []


def test_public_text_preserves_downstream_layer_boundaries() -> None:
    """Public code/docs should keep vendor and agent ownership separated."""
    offenders: list[str] = []

    for path in _iter_public_text_files(*PUBLIC_TEXT_ROOTS):
        text = path.read_text(encoding="utf-8")
        for term in BOUNDARY_DRIFT_TERMS:
            if term in text:
                offenders.append(f"{path.relative_to(PACKAGE_ROOT)}: {term}")

    assert offenders == []


def test_agentic_reinforcement_documents_layer_contract() -> None:
    """Root reinforcement guidance should keep the downstream stack boundary explicit."""
    reinforcement = AGENTIC_REINFORCEMENT.read_text(encoding="utf-8")

    for expected_text in (
        "`ExtendedData` is the root superclass and polymorphic factory.",
        "`vendor-fabric` may extend `ExtendedData` with additive provider coordination.",
        "`agentic-fabric` may extend the vendor layer with additive runtime and agent\n  behavior.",
        "Do not add vendor-aware or agent-aware branching here.",
        "Preserve `ExtendedData` factory semantics, shape promotion, and\n  built-in-to-extended round-tripping.",
    ):
        assert expected_text in reinforcement


def test_secretssync_alignment_documents_base_layer_boundary() -> None:
    """Root SecretSync guidance should keep runtime concerns out of this package."""
    alignment = SECRETSSYNC_ALIGNMENT.read_text(encoding="utf-8")

    for expected_text in (
        "`secrets-sync` owns the Go pipeline runtime, CLI, GitHub Action, deployment\n"
        "   artifacts, and the gopy binding source consumed from Python.",
        "`vendor-fabric` owns the Python facade over those bindings, plus credential\n"
        "   handoff, provider coordination, and `ExtendedData` integration.",
        "`agentic-fabric` owns framework-specific tool wrapping and runtime\n"
        "   orchestration on top of `VendorData`.",
        "`extended-data` stays the generic base layer underneath all of them.",
        "PyPI distribution: `secrets-sync-python-binding`",
        "Python import/module: `secrets_sync`",
        "`extended-data` should stay agnostic to that binding and only provide generic\n"
        "  primitives that the downstream facade layers can reuse.",
        "Do not add SecretSync-specific runtime policy here.",
    ):
        assert expected_text in alignment


def test_old_package_namespace_shims_do_not_exist() -> None:
    """Clean major-version breaks should not grow old import namespace shims."""
    offenders: list[str] = []

    for namespace in OLD_PACKAGE_NAMESPACES:
        package_path = PACKAGE_ROOT / "src" / namespace
        module_path = PACKAGE_ROOT / "src" / f"{namespace}.py"
        if package_path.exists():
            offenders.append(str(package_path.relative_to(PACKAGE_ROOT)))
        if module_path.exists():
            offenders.append(str(module_path.relative_to(PACKAGE_ROOT)))

    assert offenders == []


def test_typed_classifier_has_pep561_marker() -> None:
    """The typed package classifier should be backed by a PEP 561 marker."""
    classifiers = _pyproject()["project"]["classifiers"]

    assert "Typing :: Typed" in classifiers
    assert (PACKAGE_ROOT / "src" / "extended_data" / "py.typed").is_file()
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
            (REPO_ROOT / "docs" / "package-surface.rst").read_text(encoding="utf-8"),
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

    assert scripts == {"extended-data": "extended_data.cli:main"}


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


def test_public_guidance_does_not_claim_removed_in_package_surfaces() -> None:
    """Public docs should not describe split packages as in-package modules."""
    offenders: list[str] = []
    for path in _iter_public_text_files(REPO_ROOT / "README.md", REPO_ROOT / "docs", REPO_ROOT / "examples", REPO_ROOT / "src"):
        text = path.read_text(encoding="utf-8")
        for phrase in REMOVED_IN_PACKAGE_SURFACES:
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


def test_ownership_map_documents_moved_surfaces() -> None:
    """Moved surfaces should have explicit destination ownership in public docs."""
    ownership_map = (REPO_ROOT / "docs" / "ownership-map.rst").read_text(encoding="utf-8")

    for expected_text in (
        "jbcom/vendor-fabric",
        "vendor-fabric[...]",
        "vendor-fabric[secrets-sync]",
        "jbcom/agentic-fabric",
        "agentic-fabric[...]",
    ):
        assert expected_text in ownership_map
