# Core Examples

This directory contains working code samples for the core `extended-data`
package surface: Tier 1 primitives, Tier 2 containers, and Tier 3 file/data
processors. The examples intentionally mirror the public README and package
surface docs, so treat them as part of the documented contract.

## Examples

### Basic Usage

- [`basic_usage.py`](basic_usage.py) - Common operations with strings, lists, and maps
- [`composed_workflows.py`](composed_workflows.py) - Layered config, Terraform-style HCL, YAML-native tags, and payload pipelines
- [`serialization.py`](serialization.py) - YAML, JSON, TOML, HCL, and Base64 encoding/decoding
- [`file_operations.py`](file_operations.py) - File path utilities and Git repository helpers
- [`string_transformations.py`](string_transformations.py) - Case conversion and string manipulation

## Related Documentation

- [Package surface](../../docs/package-surface.md)
- [Repository README](../../README.md)

## Running Examples

```bash
# From the repository root, install the local package
uv sync --extra tests --extra typing

# Run a single example
uv run python examples/core/basic_usage.py

# Run the core test suite
uv run pytest tests/core
```

## Requirements

- Python 3.10-3.14
- `extended-data`
