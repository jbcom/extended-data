"""Check native distribution contents before publishing."""

from __future__ import annotations

import argparse
import re
import tarfile
import zipfile

from pathlib import Path, PurePosixPath, PureWindowsPath


PRIVATE_PARTS = {
    ".agent-state", ".claude", ".agents", ".augment", ".git", ".venv", ".tox",
    ".mcp.json", "opencode.json", "__pycache__", "node_modules", "_build", ".doctrees",
}
MACHINE_PATH = re.compile(
    rb"/(?:(?i:Users)|home)/[^\x00-\x1f/<>\"']+"
    rb"|/root(?![\w.-]|/<)"
    rb"|/private/(?:tmp|var)/"
    rb"|(?i:(?:[a-z]:[\\/]+|\\+)users[\\/]+)[^\x00-\x1f\\/<>\"']+",
)


def _contains_machine_path(data: bytes) -> bool:
    """Recognize paths in plain, JSON-escaped and Unicode-encoded text."""
    representations = [data]
    if b"\x00" in data:
        for encoding in ("utf-16-le", "utf-16-be", "utf-32-le", "utf-32-be"):
            representations.append(data.decode(encoding, errors="ignore").encode())
    for representation in representations:
        normalized = re.sub(
            rb"\\u([0-9a-fA-F]{4})",
            lambda match: chr(int(match[1], 16)).encode(errors="surrogatepass"),
            representation,
        )
        normalized = re.sub(rb"\\+/", b"/", normalized)
        if MACHINE_PATH.search(normalized):
            return True
    return False


def verify_archive(path: Path) -> list[str]:
    """Return privacy and package-surface errors for one wheel or sdist."""
    errors: list[str] = []
    names: set[str] = set()
    module = path.name.split("-", 1)[0]
    is_wheel = path.suffix == ".whl"

    def inspect(name: str, data: bytes) -> None:
        member = PurePosixPath(name)
        windows_member = PureWindowsPath(name)
        names.add(name)
        parts = {*member.parts, *(part.casefold() for part in windows_member.parts)}
        if member.is_absolute() or windows_member.root or ".." in parts or PRIVATE_PARTS.intersection(parts):
            errors.append(f"{path.name}: forbidden member {name}")
        if _contains_machine_path(name.encode()) or _contains_machine_path(data):
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
