# Input Examples

This directory contains working examples for `InputProvider` and the decorator
helpers in `extended_data.inputs`.

## Running Examples

All examples can be run as Python modules from the project root:

```bash
# Install the local package first
uv sync --extra tests

# Run examples
uv run python examples/inputs/basic_usage.py
uv run python examples/inputs/decorator_api.py
uv run python examples/inputs/encoding_decoding.py
```

## Available Examples

### basic_usage.py

Demonstrates the `InputProvider` API:
- Loading inputs from environment variables
- Environment variable prefix filtering
- Direct `ExtendedDict`/`ExtendedString` input snapshot access with `snapshot_inputs()`
- Active input replacement with `replace_inputs()`
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
- Tier 2 reconstruction/export methods on decoded inputs
- Promoted default values for missing inputs
