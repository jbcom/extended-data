"""Top-level command line interface for Extended Data."""

from __future__ import annotations

import argparse
import sys

from collections.abc import Sequence
from typing import Any, cast

from extended_data.io import DataFile
from extended_data.primitives.redaction import redact_sensitive_text
from extended_data.workflows import DataWorkflow, WorkflowResult, list_data_transform_steps


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
        _write_stdout(artifact.wrap_for_export(allow_encoding=args.output, **_json_format_opts(args)))
        return 0
    except Exception as e:
        _write_stderr(str(e))
        return 1


def cmd_inspect(args: argparse.Namespace) -> int:
    """Decode structured data and write its DataFile metadata."""
    try:
        artifact = _decode_artifact(args)
        _write_stdout(artifact.metadata.wrap_for_export(allow_encoding=args.output, **_json_format_opts(args)))
        return 0
    except Exception as e:
        _write_stderr(str(e))
        return 1


def _json_format_opts(args: argparse.Namespace) -> dict[str, Any]:
    """Return common JSON formatting options for CLI export commands."""
    if args.output == "json" and not args.compact:
        return {"indent_2": True}
    return {}


def _merge_workflow(args: argparse.Namespace) -> DataWorkflow:
    """Build a layered merge workflow from CLI arguments."""
    file_paths = args.file_paths
    if len(file_paths) < 2:
        raise ValueError("merge requires at least two files")

    workflow = DataWorkflow.from_file(file_paths[0], suffix=args.suffix)
    for file_path in file_paths[1:]:
        workflow = workflow.merge_file(file_path, suffix=args.suffix)
    return workflow


def cmd_merge(args: argparse.Namespace) -> int:
    """Merge structured files through DataWorkflow and write or print the result."""
    try:
        workflow = _merge_workflow(args)
        result: WorkflowResult
        if args.write:
            result = workflow.write(args.write, encoding=args.output, allow_empty=args.allow_empty)
        else:
            result = workflow.result()
        _write_stdout(result.wrap_for_export(allow_encoding=args.output, **_json_format_opts(args)))
        return 0
    except Exception as e:
        _write_stderr(str(e))
        return 1


def _transform_workflow(args: argparse.Namespace) -> DataWorkflow:
    """Build a workflow that applies named Tier 2 transforms."""
    steps = args.steps or []
    if not steps:
        raise ValueError("transform requires at least one --step")

    return _decode_artifact(args).workflow().transform(*steps)


def cmd_transform(args: argparse.Namespace) -> int:
    """Apply named Tier 2 transforms through DataWorkflow."""
    try:
        workflow = _transform_workflow(args)
        result: WorkflowResult
        if args.write:
            result = workflow.write(args.write, encoding=args.output, allow_empty=args.allow_empty)
        else:
            result = workflow.result()
        _write_stdout(result.wrap_for_export(allow_encoding=args.output, **_json_format_opts(args)))
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
  extended-data inspect --file config.yaml
  extended-data merge base.yaml env.yaml --output yaml
  extended-data transform --file payload.json --step reconstruct --step unhump
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

    inspect_parser = subparsers.add_parser("inspect", help="Decode data and print artifact metadata")
    inspect_parser.add_argument("value", nargs="?", help="Inline payload to inspect")
    inspect_parser.add_argument("--file", dest="file_path", help="File path or URL to inspect")
    inspect_parser.add_argument("--suffix", help="Input format override")
    inspect_parser.add_argument("--output", choices=OUTPUT_ENCODINGS, default="json", help="Output encoding")
    inspect_parser.add_argument("--compact", action="store_true", help="Compact JSON output")
    inspect_parser.set_defaults(func=cmd_inspect)

    merge_parser = subparsers.add_parser("merge", help="Deep merge structured files")
    merge_parser.add_argument("file_paths", nargs="+", help="Structured files to merge in order")
    merge_parser.add_argument("--suffix", help="Input format override for all files")
    merge_parser.add_argument("--output", choices=OUTPUT_ENCODINGS, default="json", help="Output encoding")
    merge_parser.add_argument("--compact", action="store_true", help="Compact JSON output")
    merge_parser.add_argument("--write", help="Write merged output to this file")
    merge_parser.add_argument("--allow-empty", action="store_true", help="Allow writing empty merged output")
    merge_parser.set_defaults(func=cmd_merge)

    transform_parser = subparsers.add_parser("transform", help="Apply named Extended Data transforms")
    transform_parser.add_argument("value", nargs="?", help="Inline payload to transform")
    transform_parser.add_argument("--file", dest="file_path", help="File path or URL to transform")
    transform_parser.add_argument("--suffix", help="Input format override")
    transform_parser.add_argument(
        "--step",
        dest="steps",
        action="append",
        choices=list_data_transform_steps(),
        help="Transform step to apply in order",
    )
    transform_parser.add_argument("--output", choices=OUTPUT_ENCODINGS, default="json", help="Output encoding")
    transform_parser.add_argument("--compact", action="store_true", help="Compact JSON output")
    transform_parser.add_argument("--write", help="Write transformed output to this file")
    transform_parser.add_argument("--allow-empty", action="store_true", help="Allow writing empty transformed output")
    transform_parser.set_defaults(func=cmd_transform)

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
