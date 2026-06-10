# Examples

This directory contains working examples demonstrating the features of `Extended Data inputs`.

## Running Examples

All examples can be run as Python modules from the project root:

```bash
# Install the package first
uv sync

# Run examples
uv run python -m examples.basic_usage
uv run python -m examples.decorator_api
uv run python -m examples.encoding_decoding
```

## Available Examples

### basic_usage.py

Demonstrates the `InputProvider` API:
- Loading inputs from environment variables
- Environment variable prefix filtering
- Type conversion (boolean, integer, float)
- Default values
- Input freezing and thawing

### decorator_api.py

Demonstrates the modern decorator-based API:
- `@directed_inputs` class decorator
- `@input_config` method decorator for fine-grained control
- Automatic parameter injection
- Required inputs with custom source names
- JSON decoding
- Type coercion
- Runtime input overrides

### encoding_decoding.py

Demonstrates input decoding capabilities:
- JSON decoding
- YAML decoding
- Base64 decoding
- Combined Base64 + JSON/YAML decoding
- Default values for missing inputs
