# Logging Examples

This directory contains working examples for structured lifecycle logging in
`extended_data.logging`.

`Logging` does not write log files by default. Pass `enable_file=True` with an
optional `log_file_name`, or set `OVERRIDE_TO_FILE=True`, when a workflow should
create file output.

## Examples

### basic_logging.py

Demonstrates fundamental logging capabilities:
- Logging messages at different levels (debug, info, warning, error)
- Attaching JSON data to log messages
- Using labeled JSON data
- Adding identifiers to messages

```bash
uv run python examples/logging/basic_logging.py
```

### markers_and_storage.py

Shows how to use markers for message organization:
- Context markers to prefix messages with labels
- Storage markers to collect messages for later retrieval
- Combining both marker types

```bash
uv run python examples/logging/markers_and_storage.py
```

### verbosity_control.py

Demonstrates verbosity settings:
- Setting verbosity thresholds
- Using verbose messages
- Registering bypass markers that ignore verbosity settings

```bash
uv run python examples/logging/verbosity_control.py
```

### exit_run_formatting.py

Shows result formatting and transformation:
- Key transformations (snake_case, camel_case, etc.)
- Nested key transformation
- Adding prefixes to keys
- Custom transform functions

```bash
uv run python examples/logging/exit_run_formatting.py
```

## Running the Examples

1. Install the package:
   ```bash
   pip install extended-data
   ```

2. Run any example:
   ```bash
   python examples/logging/<example_name>.py
   ```

Or from the repository root:
```bash
uv run python examples/logging/<example_name>.py
```
