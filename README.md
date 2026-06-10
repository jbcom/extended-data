# Extended Data

Comprehensive Python data utilities for serialization, configuration inputs,
structured logging, vendor data connectors, and workflow-oriented integrations.

This repository is the clean major-version consolidation of the previous
`extended-data-library` Python packages. The old package namespaces are not
preserved; the public API now lives under `extended_data`.

## Install

```bash
pip install extended-data
```

Optional integrations are installed by feature:

```bash
pip install "extended-data[aws,github,vault]"
pip install "extended-data[google,slack,zoom]"
pip install "extended-data[ai]"
pip install "extended-data[meshy,mcp]"
pip install "extended-data[secrets]"
```

## Usage

```python
from extended_data import ConnectorFabric, InputProvider, Logging, decode_json, encode_yaml

logger = Logging(logger_name="example")
inputs = InputProvider(inputs={"GITHUB_OWNER": "jbcom"}, from_environment=False)
connectors = ConnectorFabric(inputs=inputs.inputs, logger=logger)
data = decode_json('{"status": "ok"}')

print(encode_yaml(data))
```

The fabric can also instantiate any registered connector by name:

```python
github = connectors.get_connector(
    "github",
    github_owner="jbcom",
    github_token="...",
)
```

Connector names are normalized before lookup. If a known built-in connector is
requested without its optional extra installed, the registry raises an
`ImportError` with the matching `extended-data[...]` install target.

Inspect connector availability before wiring vendor workflows:

```python
catalog = connectors.list_connector_info()
github_info = connectors.get_connector_info("github")
```

The same catalog is available from the CLI:

```bash
extended-data list
extended-data info github --json
```

## Package Shape

```text
extended_data/
  core serialization, files, types, transforms
  inputs/       InputProvider and decorator-based input injection
  logging/      structured lifecycle logging
  connectors/   ConnectorFabric and vendor adapters
  secrets/      Python access to secret sync primitives
  workflows/    higher-order workflow composition
```

Vendor connectors are first-class adapters in the data fabric. `ConnectorFabric`
uses the registry to resolve connectors by name, injects shared input/logging
context, caches connector instances, and lets specialized helpers coexist with
generic vendor lookup.

More detail lives in [`docs/package-surface.md`](docs/package-surface.md).

## Development

```bash
uv sync --extra tests --extra typing
uv run pytest
uv run ruff check src tests
uv build
```

## License

MIT.
