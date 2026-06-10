#!/usr/bin/env python3
"""Example: Running the Meshy MCP Server.

This example demonstrates how to run the Model Context Protocol (MCP)
server for Meshy AI, enabling integration with Claude Desktop and
other MCP-compatible clients.

Requirements:
    pip install extended-data[meshy,mcp]

Environment Variables:
    MESHY_API_KEY: Your Meshy API key

Usage:
    # Run the server (connects via stdio)
    python examples/mcp_server.py

    # Or use the installed command
    meshy-mcp

    # Configure in Claude Desktop's config.json:
    {
        "mcpServers": {
            "meshy": {
                "command": "meshy-mcp",
                "env": {
                    "MESHY_API_KEY": "<your-key-here>"
                }
            }
        }
    }
"""

from __future__ import annotations

import os
import sys


def main() -> int:
    """Run the Meshy MCP server."""
    # Check for required environment variables
    if not os.getenv("MESHY_API_KEY"):
        print("Error: MESHY_API_KEY environment variable is required.")
        return 1

    try:
        from extended_data.connectors.meshy.mcp import run_server
    except ImportError:
        print("Error: Could not import MCP server. Install with: pip install extended-data[meshy,mcp]")
        return 1

    print("Starting Meshy MCP server...")
    try:
        # Run the server (blocks until stopped)
        run_server()
    except KeyboardInterrupt:
        pass

    print("\nMCP server stopped.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
