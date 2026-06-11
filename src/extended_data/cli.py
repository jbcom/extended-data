"""Top-level command line interface for Extended Data."""

from __future__ import annotations

import argparse
import sys

from collections.abc import Sequence
from typing import Any, cast

from extended_data.io import DataFile
from extended_data.primitives.redaction import redact_sensitive_text


CONNECTOR_COMMANDS = frozenset({"call", "info", "list", "mcp", "methods"})
OUTPUT_ENCODINGS = ("json", "yaml", "toml", "hcl", "raw")


def _write_stdout(message: str) -> None:
    """Write one CLI output line."""
    sys.stdout.write(f"{message}\n")


def _write_stderr(message: str) -> None:
    """Write one CLI error line."""
    sys.stderr.write(f"{redact_sensitive_text(message)}\n")


def _decode_artifact(args: argparse.Namespace) -> DataFile:
    """Decode an inline payload or file path into a DataFile artifact."""
    value = getattr(args, "value", None)
    file_path = getattr(args, "file_path", None)

    if value is not None and file_path is not None:
        raise ValueError("pass either VALUE or --file, not both")
    if value is None and file_path is None:
        raise ValueError("pass VALUE or --file")
    if file_path is not None:
        return DataFile.read(file_path, suffix=args.suffix)
    return DataFile.decode(cast(str, value), suffix=args.suffix)


def cmd_decode(args: argparse.Namespace) -> int:
    """Decode structured data and write it through the shared export boundary."""
    try:
        artifact = _decode_artifact(args)
        format_opts: dict[str, Any] = {}
        if args.output == "json" and not args.compact:
            format_opts["indent_2"] = True
        _write_stdout(artifact.wrap_for_export(allow_encoding=args.output, **format_opts))
        return 0
    except Exception as e:
        _write_stderr(str(e))
        return 1


def _build_parser() -> argparse.ArgumentParser:
    """Build the top-level Extended Data argument parser."""
    parser = argparse.ArgumentParser(
        prog="extended-data",
        description="CLI for Extended Data primitives, files, workflows, and connectors",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  extended-data decode '{"service": {"name": "api"}}' --suffix json
  extended-data decode --file config.yaml --output json
  extended-data list --category cloud
  extended-data call github get_repository_file --path service.json --json
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    decode_parser = subparsers.add_parser("decode", help="Decode inline data or a file")
    decode_parser.add_argument("value", nargs="?", help="Inline payload to decode")
    decode_parser.add_argument("--file", dest="file_path", help="File path or URL to decode")
    decode_parser.add_argument("--suffix", help="Input format override")
    decode_parser.add_argument("--output", choices=OUTPUT_ENCODINGS, default="json", help="Output encoding")
    decode_parser.add_argument("--compact", action="store_true", help="Compact JSON output")
    decode_parser.set_defaults(func=cmd_decode)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Extended Data CLI."""
    args = list(argv) if argv is not None else sys.argv[1:]
    if args and args[0] in CONNECTOR_COMMANDS:
        from extended_data.connectors.cli import main as connectors_main

        return connectors_main(args)

    parser = _build_parser()
    parsed = parser.parse_args(args)

    if not parsed.command:
        parser.print_help()
        return 0

    try:
        return parsed.func(parsed)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
