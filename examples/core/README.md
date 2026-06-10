# Extended Data Types Examples

This directory contains working code samples demonstrating the capabilities of
the `Extended Data core` library. The examples intentionally mirror the public
guides and are part of the documented contract, not throwaway snippets.

## Examples

### Basic Usage

- [`basic_usage.py`](basic_usage.py) - Common operations with strings, lists, and maps
- [`composed_workflows.py`](composed_workflows.py) - Layered config, Terraform-style HCL, YAML-native tags, and payload pipelines
- [`serialization.py`](serialization.py) - YAML, JSON, TOML, HCL, and Base64 encoding/decoding
- [`file_operations.py`](file_operations.py) - File path utilities and Git repository helpers
- [`string_transformations.py`](string_transformations.py) - Case conversion and string manipulation

## Related Documentation

- [Package docs](https://extended-data.dev/core/data-types/)
- [Getting started](https://extended-data.dev/getting-started/)
- [Packages overview](https://extended-data.dev/packages/)

## Running Examples

```bash
# From the repository root, run the full example suite
tox -e edt-examples

# Or run a single example with the prepared tox environment
uv run python examples/core/basic_usage.py
```

## Requirements

- Python 3.10-3.14
- Extended Data core package
