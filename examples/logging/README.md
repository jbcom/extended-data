# LifecycleLogging Examples

This directory contains working examples demonstrating the features of the `extended_data.logging` package.

## Examples

### basic_logging.py

Demonstrates fundamental logging capabilities:
- Logging messages at different levels (debug, info, warning, error)
- Attaching JSON data to log messages
- Using labeled JSON data
- Adding identifiers to messages

```bash
python examples/basic_logging.py
```

### markers_and_storage.py

Shows how to use markers for message organization:
- Context markers to prefix messages with labels
- Storage markers to collect messages for later retrieval
- Combining both marker types

```bash
python examples/markers_and_storage.py
```

### verbosity_control.py

Demonstrates verbosity settings:
- Setting verbosity thresholds
- Using verbose messages
- Registering bypass markers that ignore verbosity settings

```bash
python examples/verbosity_control.py
```

### exit_run_formatting.py

Shows result formatting and transformation:
- Key transformations (snake_case, camel_case, etc.)
- Nested key transformation
- Adding prefixes to keys
- Custom transform functions

```bash
python examples/exit_run_formatting.py
```

## Running the Examples

1. Install the package:
   ```bash
   pip install extended_data.logging
   ```

2. Run any example:
   ```bash
   python examples/<example_name>.py
   ```

Or from the repository root:
```bash
uv run python examples/<example_name>.py
```
