"""Check native distribution contents before publishing."""

from __future__ import annotations

import argparse
import re
import tarfile
import zipfile

from pathlib import Path, PurePosixPath


PRIVATE_PARTS = {
    ".agent-state", ".claude", ".agents", ".augment", ".git", ".venv", ".tox",
    ".mcp.json", "opencode.json", "__pycache__", "node_modules", "_build", ".doctrees",
}
MACHINE_PATH = re.compile(rb"/Users/[A-Za-z][^/\s]*/|/private/(?:tmp|var)/")


def verify_archive(path: Path) -> list[str]:
    """Return privacy and package-surface errors for one wheel or sdist."""
    errors: list[str] = []
    names: set[str] = set()
    module = path.name.split("-", 1)[0]
    is_wheel = path.suffix == ".whl"

    def inspect(name: str, data: bytes) -> None:
        member = PurePosixPath(name)
        names.add(name)
        if member.is_absolute() or ".." in member.parts or PRIVATE_PARTS.intersection(member.parts):
            errors.append(f"{path.name}: forbidden member {name}")
        if MACHINE_PATH.search(data):
            errors.append(f"{path.name}: machine path in {name}")

    if is_wheel:
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                inspect(name, archive.read(name))
        required = {f"{module}/__init__.py"}
    else:
        with tarfile.open(path, "r:gz") as archive:
            for member in archive.getmembers():
                if not member.isfile():
                    errors.append(f"{path.name}: unsupported member {member.name}")
                    continue
                stream = archive.extractfile(member)
                if stream is not None:
                    inspect(member.name, stream.read())
        root = path.name.removesuffix(".tar.gz")
        required = {f"{root}/src/{module}/__init__.py", f"{root}/pyproject.toml", f"{root}/README.md"}
    errors.extend(f"{path.name}: missing {name}" for name in sorted(required - names))
    return errors


def verify_directory(directory: Path) -> list[str]:
    """Require a complete wheel/sdist pair and inspect each artifact."""
    errors: list[str] = []
    for pattern in ("*.whl", "*.tar.gz"):
        artifacts = sorted(directory.glob(pattern))
        if len(artifacts) != 1:
            errors.append(f"{directory}: expected one {pattern}, found {len(artifacts)}")
        for artifact in artifacts:
            errors.extend(verify_archive(artifact))
    return errors


def main() -> int:
    """Validate package build directories supplied on the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", nargs="+", type=Path)
    arguments = parser.parse_args()
    errors = [error for directory in arguments.directories for error in verify_directory(directory)]
    for error in errors:
        print(error)
    if errors:
        return 1
    print("Native distribution contents are clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
