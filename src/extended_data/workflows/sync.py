"""Data sync primitives for local structured artifacts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from extended_data.containers import ExtendedDict, ExtendedString, extend_data, to_builtin
from extended_data.io.exporters import wrap_raw_data_for_export
from extended_data.io.files import DataFile, FilePath, read_file, resolve_local_path, write_file
from extended_data.primitives.redaction import redact_sensitive_data, redact_sensitive_text
from extended_data.primitives.serialization import normalize_data_encoding
from extended_data.primitives.state import is_nothing


@dataclass(frozen=True, slots=True)
class DataSyncResult:
    """Result from a local data sync operation."""

    source: ExtendedString
    destination: ExtendedString
    changed: bool
    dry_run: bool = False
    bytes_written: int = 0
    encoding: ExtendedString = field(default_factory=lambda: ExtendedString("raw"))
    output_path: Path | None = None
    metadata: ExtendedDict = field(default_factory=ExtendedDict)

    def to_dict(self) -> ExtendedDict:
        """Return this result as promoted Extended Data."""
        return extend_data(
            {
                "source": self.source,
                "destination": self.destination,
                "changed": self.changed,
                "dry_run": self.dry_run,
                "bytes_written": self.bytes_written,
                "encoding": self.encoding,
                "output_path": str(self.output_path) if self.output_path is not None else None,
                "metadata": self.metadata,
            }
        )


def sync_value_to_file(
    value: Any,
    file_path: FilePath,
    *,
    source: str = "memory",
    encoding: str | None = None,
    charset: str = "utf-8",
    allow_empty: bool = False,
    dry_run: bool = False,
    tld: Path | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> DataSyncResult:
    """Sync a value to a local file only when the rendered bytes change."""
    if is_nothing(value) and not allow_empty:
        raise ValueError("sync_value_to_file received empty data; pass allow_empty=True to sync it")

    resolved_encoding = _sync_encoding(file_path, encoding)
    rendered = _render_sync_value(value, allow_encoding=resolved_encoding)
    output_path = resolve_local_path(file_path, tld=tld)
    existing = _read_existing_text(output_path, charset=charset)
    changed = existing != rendered

    if changed and not dry_run:
        write_file(file_path, value, encoding=resolved_encoding, charset=charset, allow_empty=allow_empty, tld=tld)

    return DataSyncResult(
        source=ExtendedString(redact_sensitive_text(source)),
        destination=ExtendedString(redact_sensitive_text(file_path)),
        changed=changed,
        dry_run=dry_run,
        bytes_written=len(rendered.encode(charset)) if changed else 0,
        encoding=ExtendedString(resolved_encoding),
        output_path=output_path,
        metadata=ExtendedDict(redact_sensitive_data(metadata or {})),
    )


def sync_file_to_file(
    source_path: FilePath,
    destination_path: FilePath,
    *,
    suffix: str | None = None,
    encoding: str | None = None,
    charset: str = "utf-8",
    errors: str = "strict",
    allow_empty: bool = False,
    dry_run: bool = False,
    tld: Path | None = None,
) -> DataSyncResult:
    """Read a structured file and sync its decoded value to another file."""
    artifact = DataFile.read(source_path, suffix=suffix, charset=charset, errors=errors, tld=tld)
    return sync_value_to_file(
        artifact.as_builtin(),
        destination_path,
        source=str(artifact.source),
        encoding=encoding,
        charset=charset,
        allow_empty=allow_empty,
        dry_run=dry_run,
        tld=tld,
        metadata=artifact.metadata,
    )


def _sync_encoding(file_path: FilePath, encoding: str | None) -> str:
    if encoding is not None:
        return normalize_data_encoding(encoding) or "raw"
    from extended_data.io.files import get_encoding_for_file_path

    return get_encoding_for_file_path(file_path)


def _render_sync_value(value: Any, *, allow_encoding: str) -> str:
    if allow_encoding == "raw" and isinstance(value, str):
        return value
    return wrap_raw_data_for_export(to_builtin(value), allow_encoding=allow_encoding)


def _read_existing_text(path: Path, *, charset: str) -> str | None:
    if not path.exists():
        return None
    contents = read_file(path, charset=charset)
    if contents is None:
        return None
    if not isinstance(contents, str):
        raise TypeError(f"Expected text while reading {path}")
    return contents
