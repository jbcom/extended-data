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
pip install "extended-data[ai]"        # LangChain, MCP, and Strands
pip install "extended-data[meshy,mcp]"
pip install "extended-data[secrets]"
```

CrewAI adapters remain available when `crewai` is installed independently, but
`extended-data` intentionally does not publish a CrewAI extra while current
CrewAI releases pull vulnerable `chromadb` versions transitively.

## Usage

```python
from extended_data import ConnectorFabric, DataWorkflow, ExtendedDict, InputProvider, Logging, decode_file, decode_json, encode_yaml

logger = Logging(logger_name="example")
inputs = InputProvider(inputs={"GITHUB_OWNER": "jbcom"}, from_environment=False)
connectors = ConnectorFabric(inputs=inputs.inputs, logger=logger)
data = decode_json('{"status": "ok"}')
payload = ExtendedDict(data).deep_merge({"source": "example"})
decoded_file = decode_file('{"service": {"name": "api"}}', suffix="json", as_extended=True)
workflow = DataWorkflow.from_value(payload).then(("normalize", lambda data: data.unhump())).result()

print(encode_yaml(payload.data))
print(decoded_file["service"]["name"].upper_first())
print(workflow.as_builtin())
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
  primitives/   Tier 1 pure functions and codecs
  containers/   Tier 2 ExtendedString/Dict/List/Set wrappers
  io/           Tier 3 file, import, export, and base64 processors
  inputs/       InputProvider and decorator-based input injection
  logging/      structured lifecycle logging
  connectors/   Tier 3 ConnectorFabric and vendor adapters
  secrets/      Python access to secret sync primitives
  workflows/    Tier 3 higher-order workflow composition
```

Vendor connectors are first-class adapters in the data fabric. `ConnectorFabric`
uses the registry to resolve connectors by name, injects shared input/logging
context, caches connector instances, and lets specialized helpers coexist with
generic vendor lookup.

The `secrets` connector integrates with the standalone `secretsync` CLI or
native bindings. CLI fallback expects `secretsync pipeline --output json` to
return the stable pipeline result envelope used by this package.

The package is intentionally tiered:

- Tier 1 functions stay stateless and composable.
- Tier 2 containers inherit Python's user container types and expose ergonomic
  methods over Tier 1 functions.
- Tier 3 processors use the first two tiers to handle files, inputs, API data,
  vendor integrations, and workflows.

Tier 3 decoders can opt into Tier 2 containers with `as_extended=True`, so
decoded files, Base64 payloads, and directed inputs can immediately use
`ExtendedDict`, `ExtendedList`, `ExtendedSet`, and `ExtendedString` methods.
`DataWorkflow` makes those compositions first-class: read or decode data,
apply named transformations, write an output artifact, and keep the step trail
in a `WorkflowResult`. Missing workflow inputs and empty writes fail loudly.

More detail lives in [`docs/package-surface.md`](docs/package-surface.md).

## Development

```bash
uv sync --extra tests --extra typing
uv run pytest
uv run ruff check src tests
uv run mypy src/extended_data
uv build
```

## License

MIT.
