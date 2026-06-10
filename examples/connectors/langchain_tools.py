#!/usr/bin/env python3
"""Example: Using Meshy Tools with LangChain Agents.

This example demonstrates how to use Meshy AI tools with LangChain
to create an AI agent capable of generating 3D assets.

Requirements:
    pip install extended-data[meshy,langchain]
    pip install langchain-anthropic  # For Claude as the LLM

Environment Variables:
    MESHY_API_KEY: Your Meshy API key
    ANTHROPIC_API_KEY: Your Anthropic API key (for Claude)
"""

from __future__ import annotations

import os
import sys


def main() -> int:
    """Demonstrate LangChain integration with Meshy tools."""
    # Check for required environment variables
    missing = []
    if not os.getenv("MESHY_API_KEY"):
        missing.append("MESHY_API_KEY")
    if not os.getenv("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")

    if missing:
        print(f"Error: Missing required environment variables: {', '.join(missing)}")
        return 1

    try:
        from langchain_anthropic import ChatAnthropic
        from langgraph.prebuilt import create_react_agent

        from extended_data.connectors.meshy.tools import get_tools
    except ImportError:
        print("Error: Could not import required packages.")
        print("Install with: pip install extended-data[meshy,langchain] langchain-anthropic")
        return 1

    # Get Meshy tools for LangChain
    tools = get_tools()
    print(f"Loaded {len(tools)} Meshy tools for LangChain.")

    # Create the LLM
    llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)

    # Create the agent
    agent = create_react_agent(llm, tools)

    # Run a query
    query = "Generate a 3D model of a red sports car in preview mode"
    print(f"\nSending query: '{query}'")

    try:
        result = agent.invoke({"messages": [("user", query)]})

        # Print the response
        for message in result["messages"]:
            if hasattr(message, "content") and message.content:
                role = message.__class__.__name__.replace("Message", "")
                if len(message.content) > 500:
                    print(f"\n[{role}] {message.content[:500]}... (truncated)")
                else:
                    print(f"\n[{role}] {message.content}")

    except Exception as e:
        print(f"Error running agent: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
