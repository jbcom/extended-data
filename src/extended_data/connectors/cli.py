"""Unified CLI for Extended Data Connectors.

This module provides a command-line interface to all extended data connectors
using the central registry for discovery.

Usage:
    # List available connectors
    extended-data list

    # Call any connector method
    extended-data call <connector> <method> [--arg value ...]

    # Interactive mode
    extended-data shell

    # Start MCP server
    extended-data mcp

    # Specific connector shortcuts (if implemented)
    extended-data jules sources
    extended-data cursor agents
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from typing import Any

from extended_data.connectors.registry import (
    get_connector,
    get_connector_class,
    list_connector_info,
)


def _json_output(data: Any) -> str:
    """Format data as JSON for output."""
    if hasattr(data, "model_dump"):
        data = data.model_dump()
    elif hasattr(data, "__iter__") and not isinstance(data, (str, dict)):
        data = [d.model_dump() if hasattr(d, "model_dump") else d for d in data]
    return json.dumps(data, indent=2, default=str)


def _parse_arg_value(value: str) -> Any:
    """Parse a CLI argument value, attempting JSON decode."""
    # Try JSON first
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        pass

    # Try common conversions
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    return value


# =============================================================================
# Commands
# =============================================================================


def cmd_list(args: argparse.Namespace) -> int:
    """List available connectors."""
    info = list_connector_info()

    if args.json:
        return 0

    for c in info:
        env = c.get("api_key_env") or "-"
        "✓" if os.environ.get(env) else " "

    return 0


def cmd_call(args: argparse.Namespace) -> int:
    """Call a connector method."""
    connector_name = args.connector
    method_name = args.method

    # Parse extra arguments
    kwargs = {}
    extra = args.extra or []
    i = 0
    while i < len(extra):
        arg = extra[i]
        if arg.startswith("--"):
            key = arg[2:].replace("-", "_")
            if i + 1 < len(extra) and not extra[i + 1].startswith("--"):
                kwargs[key] = _parse_arg_value(extra[i + 1])
                i += 2
            else:
                kwargs[key] = True
                i += 1
        else:
            i += 1

    try:
        connector = get_connector(connector_name)
        method = getattr(connector, method_name, None)

        if method is None:
            return 1

        method(**kwargs)
        return 0

    except Exception:
        return 1


def cmd_methods(args: argparse.Namespace) -> int:
    """List methods for a connector."""
    connector_name = args.connector

    try:
        cls = get_connector_class(connector_name)
    except ValueError:
        return 1

    for name in sorted(dir(cls)):
        if name.startswith("_"):
            continue
        attr = getattr(cls, name, None)
        if not callable(attr) or isinstance(attr, type):
            continue

        # Get first line of docstring
        if attr.__doc__:
            attr.__doc__.split("\n")[0].strip()[:50]

    return 0


def cmd_mcp(args: argparse.Namespace) -> int:
    """Start MCP server."""
    from extended_data.connectors.mcp import main as mcp_main

    return mcp_main()


def cmd_info(args: argparse.Namespace) -> int:
    """Show info about a specific connector."""
    from extended_data.connectors.registry import get_connector_info

    try:
        get_connector_info(args.connector)
        return 0
    except ValueError:
        return 1


# =============================================================================
# Main CLI
# =============================================================================


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="extended-data",
        description="Unified CLI for all extended data connectors",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  extended-data list                    # List all connectors
  extended-data methods jules           # List Jules methods
  extended-data call jules list_sources # Call a method
  extended-data call cursor list_agents
  extended-data mcp                     # Start MCP server
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List available connectors")
    list_parser.add_argument("--json", action="store_true", help="JSON output")
    list_parser.set_defaults(func=cmd_list)

    # Methods command
    methods_parser = subparsers.add_parser("methods", help="List methods for a connector")
    methods_parser.add_argument("connector", help="Connector name")
    methods_parser.set_defaults(func=cmd_methods)

    # Info command
    info_parser = subparsers.add_parser("info", help="Show connector info")
    info_parser.add_argument("connector", help="Connector name")
    info_parser.set_defaults(func=cmd_info)

    # Call command
    call_parser = subparsers.add_parser("call", help="Call a connector method")
    call_parser.add_argument("connector", help="Connector name")
    call_parser.add_argument("method", help="Method name")
    call_parser.add_argument("extra", nargs="*", help="Method arguments (--arg value)")
    call_parser.set_defaults(func=cmd_call)

    # MCP command
    mcp_parser = subparsers.add_parser("mcp", help="Start MCP server")
    mcp_parser.set_defaults(func=cmd_mcp)

    # Parse and execute
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if hasattr(args, "func"):
        try:
            return args.func(args)
        except KeyboardInterrupt:
            return 130
        except Exception:
            return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
