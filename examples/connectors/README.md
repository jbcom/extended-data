# Examples

This directory contains working examples demonstrating how to use extended-data.

## Quick Start

Install extended-data with the extras you need:

```bash
# Install with all connectors
pip install extended-data[all]

# Or install specific connectors
pip install extended-data[aws,google,meshy]

# For AI framework integration
pip install extended-data[langchain]
pip install extended-data[crewai]

# For the Meshy MCP server
pip install extended-data[meshy,mcp]
```

## Examples

### Basic Connectors

- [`basic_aws.py`](basic_aws.py) - AWS connector with Organizations and S3
- [`basic_google.py`](basic_google.py) - Google Cloud connector with Workspace and Billing
- [`basic_meshy.py`](basic_meshy.py) - Meshy AI 3D generation

### AI Agent Integration

- [`langchain_tools.py`](langchain_tools.py) - Using Meshy tools with LangChain agents
- [`mcp_server.py`](mcp_server.py) - Running the MCP server for Claude integration

## Environment Variables

Most examples require API keys set as environment variables:

```bash
# AWS
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"

# Google Cloud
export GOOGLE_SERVICE_ACCOUNT='{"type": "service_account", ...}'

# Meshy AI
export MESHY_API_KEY="msy_your_key"

# For LangChain examples
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Running Examples

```bash
# Run any example
python examples/basic_meshy.py

# Run with debug logging
LOGLEVEL=DEBUG python examples/basic_meshy.py
```
