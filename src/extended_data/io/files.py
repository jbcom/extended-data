"""File Data Type Utilities."""

from __future__ import annotations

import os
import tempfile
import urllib.request

from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypeAlias

import validators

from git import GitCommandError, InvalidGitRepositoryError, NoSuchPathError, Repo

from extended_data.primitives.serialization import normalize_data_encoding


FilePath: TypeAlias = str | os.PathLike[str]
"""Type alias for file paths that can be represented as strings or os.PathLike objects."""


def get_parent_repository(file_path: FilePath | None = None, search_parent_directories: bool = True) -> Repo | None:
    """Retrieves the Git repository object for a given path.

    Args:
        file_path (FilePath | None): The path to a file or directory within the repository.
            If None, defaults to the current working directory.
        search_parent_directories (bool): Whether to search parent directories for the Git repository.
            Defaults to True.

    Returns:
        Repo | None: The Git repository object if found, otherwise None if the path is not a Git repository.
    """
    directory = Path(file_path) if file_path else Path.cwd()

    try:
        return Repo(str(directory), search_parent_directories=search_parent_directories)
    except (InvalidGitRepositoryError, NoSuchPathError):
        return None


def get_repository_name(repo: Repo) -> str | None:
    """Retrieves the name of the Git repository.

    Args:
        repo (Repo): The Git repository object.

    Returns:
        str | None: The name of the repository if found, otherwise None.
    """
    try:
        remote_url = next(iter(repo.remotes[0].urls))
        return Path(remote_url).stem
    except (IndexError, ValueError, StopIteration):
        return None


def clone_repository_to_temp(
    repo_owner: str, repo_name: str, github_token: str, branch: str | None = None
) -> tuple[Path, Repo]:
    """Clones a Git repository to a temporary directory for file operations.

    Args:
        repo_owner (str): The owner of the GitHub repository.
        repo_name (str): The name of the GitHub repository to clone.
        github_token (str): The GitHub token to access the repository.
        branch (str | None): The branch to clone. If None, the default branch is cloned.

    Returns:
        tuple[Path, Repo]: The path to the cloned repository's top-level directory and the Repo object.

    Raises:
        EnvironmentError: If errors occur while trying to clone a Git repository.
    """
    repo_url = f"https://{github_token}:x-oauth-basic@github.com/{repo_owner}/{repo_name}.git"

    try:
        temp_dir = Path(tempfile.mkdtemp())
        repo = Repo.clone_from(repo_url, str(temp_dir), branch=branch or None)
        return temp_dir, repo
    except GitCommandError as e:
        error_message = "Git command error occurred"
        raise OSError(error_message) from e
    except InvalidGitRepositoryError as e:
        error_message = "The repository is invalid or corrupt."
        raise OSError(error_message) from e
    except NoSuchPathError as e:
        error_message = "The specified path does not exist."
        raise OSError(error_message) from e
    except PermissionError as e:
        error_message = "Permission denied: Check your GitHub token and repository access permissions."
        raise OSError(error_message) from e


def get_tld(file_path: FilePath | None = None, search_parent_directories: bool = True) -> Path | None:
    """Retrieves the top-level directory of a Git repository.

    Args:
        file_path (FilePath | None): The path to a file or directory within the repository.
            If None, defaults to the current working directory.
        search_parent_directories (bool): Whether to search parent directories for the Git repository.
            Defaults to True.

    Returns:
        Path | None: The resolved top-level directory of the Git repository if found,
        otherwise None if the path is not a Git repository.
    """
    repo = get_parent_repository(file_path, search_parent_directories=search_parent_directories)
    return Path(repo.working_tree_dir) if repo and repo.working_tree_dir else None


def match_file_extensions(
    p: FilePath,
    allowed_extensions: list[str] | None = None,
    denied_extensions: list[str] | None = None,
) -> bool:
    """Matches the file extension of a given path against allowed or denied extensions.

    Args:
        p (FilePath): The path of the file to check.
        allowed_extensions (list[str] | None): List of allowed file extensions (without leading dot).
        denied_extensions (list[str] | None): List of denied file extensions (without leading dot).

    Returns:
        bool: True if the file's extension is allowed and not denied, otherwise False.
    """
    allowed_extensions = [ext.removeprefix(".").lower() for ext in (allowed_extensions or [])]
    denied_extensions = [ext.removeprefix(".").lower() for ext in (denied_extensions or [])]

    p = Path(p)
    suffix = (p.name.removeprefix(".") if p.name.startswith(".") else p.suffix.removeprefix(".")).lower()

    return not ((allowed_extensions and suffix not in allowed_extensions) or suffix in denied_extensions)


def get_encoding_for_file_path(file_path: FilePath) -> str:
    """Determines the encoding type based on the file extension.

    Args:
        file_path (FilePath): The path of the file to check.

    Returns:
        str: The encoding type as a string (e.g., "yaml", "json", "hcl", "toml", or "raw").
    """
    suffix = normalize_data_encoding(Path(file_path).suffix.removeprefix("."))
    if suffix in {"yaml", "json", "hcl", "toml"}:
        return suffix
    return "raw"


def file_path_depth(file_path: FilePath) -> int:
    """Calculates the depth of a given file path (the number of directories in the path).

    Args:
        file_path (FilePath): The file path to calculate depth for.

    Returns:
        int: The depth of the file path, excluding the root.
    """
    p = Path(file_path)
    parts = p.parts  # parts is a tuple of strings

    if p.is_absolute():
        # Exclude root '/' from parts
        parts = parts[1:]  # Still a tuple

    # Exclude '.' and empty strings from parts
    filtered_parts = [part for part in parts if part not in (".", "")]

    return len(filtered_parts)


def file_path_rel_to_root(file_path: FilePath) -> str:
    """Constructs a relative path to the root directory from the given file path.

    Args:
        file_path (FilePath): The file path for which to construct the relative path.

    Returns:
        str: A string representing the relative path to the root.
    """
    depth = file_path_depth(file_path)
    if depth == 0:
        return ""
    return "/".join([".."] * depth)


def resolve_local_path(file_path: FilePath, tld: Path | None = None) -> Path:
    """Resolves a file path relative to a top-level directory.

    If the path is absolute, it is returned as-is (resolved).
    If the path is relative and a tld is provided, it is resolved relative to tld.
    If the path is relative and no tld is provided, attempts to find the Git repository root.

    Args:
        file_path (FilePath): The path to resolve.
        tld (Path | None): Optional top-level directory for relative paths.
            If None, attempts to use the Git repository root.

    Returns:
        Path: The resolved absolute path.

    Raises:
        RuntimeError: If the path is relative and no tld is available.
    """
    path = Path(file_path)
    if path.is_absolute():
        return path.resolve()

    if tld is None:
        tld = get_tld()

    if tld is None:
        raise RuntimeError(f"Cannot resolve relative path '{file_path}' without a top-level directory")

    return Path(tld, file_path).resolve()


def is_url(path: str) -> bool:
    """Check if a string is a valid and safe URL.

    Uses the validators library for robust URL validation,
    restricted to HTTP/HTTPS schemes only.

    Args:
        path (str): The string to check.

    Returns:
        bool: True if the string is a valid HTTP/HTTPS URL.
    """
    if not path:
        return False
    # validators.url returns True for valid URLs, ValidationError otherwise
    result = validators.url(path)
    if result is not True:
        return False
    # Additional check: only allow http/https schemes
    return path.startswith(("http://", "https://"))


def read_file(
    file_path: FilePath,
    decode: bool = True,
    return_path: bool = False,
    charset: str = "utf-8",
    errors: str = "strict",
    headers: Mapping[str, str] | None = None,
    tld: Path | None = None,
) -> str | bytes | Path | None:
    """Reads a file from a local path or URL.

    Args:
        file_path (FilePath): The path or URL to read from.
        decode (bool): Whether to decode bytes to string. Defaults to True.
        return_path (bool): If True, returns the resolved Path object instead of contents.
        charset (str): Character encoding for decoding. Defaults to "utf-8".
        errors (str): Error handling for decoding. Defaults to "strict".
        headers (Mapping[str, str] | None): HTTP headers for URL requests.
        tld (Path | None): Top-level directory for resolving relative paths.

    Returns:
        str | bytes | Path | None: The file contents (str if decoded, bytes otherwise),
            the Path object if return_path=True, or None if the file doesn't exist.

    Raises:
        urllib.error.URLError: If the URL cannot be accessed.
        ValueError: If the URL scheme is not allowed (only http/https permitted).
    """
    path_str = str(file_path)

    # Handle URLs (is_url already validates HTTP/HTTPS only)
    if is_url(path_str):
        headers = headers or {}
        request = urllib.request.Request(path_str, headers=dict(headers))
        with urllib.request.urlopen(request) as response:
            file_data = response.read()
            if decode:
                return file_data.decode(charset, errors=errors)
            return file_data

    # Handle local files
    local_path = resolve_local_path(file_path, tld=tld)

    if return_path:
        return local_path

    if not local_path.exists():
        return None

    file_data = local_path.read_bytes()
    if decode:
        return file_data.decode(charset, errors=errors)
    return file_data


def decode_file(
    file_data: str | memoryview | bytes | bytearray,
    file_path: FilePath | None = None,
    suffix: str | None = None,
) -> Any:
    """Decodes file data based on file extension or explicit suffix.

    Supports YAML, JSON, TOML, and HCL2 formats.

    Args:
        file_data (str | memoryview | bytes | bytearray): The file contents to decode.
            This function does not read paths.
        file_path (FilePath | None): Optional file path to infer format from extension.
        suffix (str | None): Explicit format suffix (e.g., "yaml", "json", "toml", "hcl").
            Takes precedence over file_path extension.

    Returns:
        Any: The decoded data structure, or the original string if format is unknown.
    """
    # Lazy imports to avoid circular dependencies
    from extended_data.io.importers import unwrap_raw_data_from_import

    if suffix is None and file_path is not None:
        suffix = get_encoding_for_file_path(file_path)
    else:
        suffix = normalize_data_encoding(suffix)

    if suffix is not None and suffix in {"yaml", "json", "toml", "hcl", "raw"}:
        return unwrap_raw_data_from_import(file_data, encoding=suffix)
    return file_data


def write_file(
    file_path: FilePath,
    data: Any,
    encoding: str | None = None,
    charset: str = "utf-8",
    allow_empty: bool = False,
    tld: Path | None = None,
) -> Path | None:
    """Writes data to a file with automatic format encoding.

    Args:
        file_path (FilePath): The path to write to.
        data (Any): The data to write. Will be encoded based on file extension or encoding param.
        encoding (str | None): Explicit encoding format ("yaml", "json", "toml", "hcl", "raw").
            If None, inferred from file extension.
        charset (str): Character encoding for the file. Defaults to "utf-8".
        allow_empty (bool): Whether to allow writing empty data. Defaults to False.
        tld (Path | None): Top-level directory for resolving relative paths.

    Returns:
        Path | None: The path that was written to, or None if data was empty and not allowed.
    """
    from extended_data.io.exporters import wrap_raw_data_for_export
    from extended_data.primitives.state import is_nothing

    if is_nothing(data) and not allow_empty:
        return None

    resolved_encoding = get_encoding_for_file_path(file_path) if encoding is None else normalize_data_encoding(encoding)

    # Encode the data
    if resolved_encoding != "raw" and not isinstance(data, str):
        data = wrap_raw_data_for_export(data, allow_encoding=resolved_encoding)

    local_path = resolve_local_path(file_path, tld=tld)
    local_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(data, bytes):
        local_path.write_bytes(data)
    else:
        local_path.write_text(str(data), encoding=charset)

    return local_path


def delete_file(file_path: FilePath, tld: Path | None = None, missing_ok: bool = True) -> bool:
    """Deletes a file at the given path.

    Args:
        file_path (FilePath): The path to the file to delete.
        tld (Path | None): Top-level directory for resolving relative paths.
        missing_ok (bool): If True, return False when file doesn't exist.
            If False, raise FileNotFoundError when file doesn't exist. Defaults to True.

    Returns:
        bool: True if the file was deleted, False if it didn't exist (only when missing_ok=True).

    Raises:
        FileNotFoundError: If the file doesn't exist and missing_ok=False.
    """
    local_path = resolve_local_path(file_path, tld=tld)
    existed = local_path.exists()
    local_path.unlink(missing_ok=missing_ok)
    return existed
