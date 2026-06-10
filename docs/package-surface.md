# Package Surface

`extended-data` is one Python distribution with a single `extended_data`
namespace. The root package exposes the primitives users need most often:

```python
from extended_data import (
    ConnectorFabric,
    DataDecodeError,
    DataWorkflow,
    ExtendedDict,
    ExtendedList,
    ExtendedSet,
    ExtendedString,
    InputProvider,
    Logging,
    decode_json,
    extend_data,
    encode_yaml,
    flatten_map,
    to_builtin,
)
```

## Tiers

- Tier 1 `extended_data.primitives` modules are pure functions and codecs for
  strings, numbers, maps, lists, matching, state, type coercion, and structured
  formats.
- Tier 2 `extended_data.containers` classes wrap Python user containers as
  `ExtendedString`, `ExtendedDict`, `ExtendedList`, and `ExtendedSet` with
  ergonomic methods over Tier 1 primitives.
- Tier 3 processors use the first two tiers to handle files, imports, exports,
  inputs, API data, vendor integrations, and workflows.

Direct JSON, YAML, TOML, and HCL decode failures raise `DataDecodeError` with
format and position context while preserving the parser exception as the cause;
the public error message does not echo the raw payload.

```python
name = ExtendedString("API Response Value").to_snake_case()
payload = ExtendedDict({"outer": {"inner": 1}}).flatten()
items = ExtendedList([1, [2, [3]]]).flatten()
tags = ExtendedSet({"prod", "prod", ""}).compact()
```

`ExtendedDict`, `ExtendedList`, and `ExtendedSet` recursively promote nested
plain values on construction and mutation, so method chains can continue through
data loaded from normal Python literals:

```python
payload = ExtendedDict({"service": {"name": "api"}})
payload["service"]["name"].upper_first()
```

Tier 3 decode surfaces can promote plain decoded values into Tier 2 containers:

```python
from extended_data import decode_file

payload = decode_file('{"service": {"name": "api"}}', suffix="json", as_extended=True)
assert payload["service"]["name"].upper_first() == "Api"
```

Use `extend_data(value)` to promote existing plain data and `to_builtin(value)`
to lower extended containers back to standard Python data.

`DataWorkflow` is the Tier 3 composition surface for higher-order data
processing. It reads or decodes structured data through the file and format
processors, promotes values into Tier 2 containers by default, applies named
transformation steps, writes output artifacts, and returns a `WorkflowResult`
with the completed value, output path, and step trail.

```python
from extended_data import DataWorkflow

env_data = DataWorkflow.from_file("config/dev.yaml").value
result = (
    DataWorkflow.from_file("config/base.yaml")
    .then(("merge-env", lambda data: data.deep_merge(env_data)))
    .write("build/config.yaml")
)

assert result.steps == ("read:config/base.yaml", "merge-env", "write:build/config.yaml")
```

Missing workflow input files raise `FileNotFoundError`, and empty workflow
writes raise `ValueError` unless `allow_empty=True` is passed.

`InputProvider` loads input data from explicit mappings, environment variables,
and stdin, then decodes or coerces values through the primitive layer. Its
`decode_input(..., as_extended=True)` path gives input-driven workflows the same
container bridge as file and Base64 decoding. Requested input coercions are
strict, and diagnostics identify the input key and failed operation without
echoing raw values from environment variables, stdin, JSON, YAML, or Base64
payloads. `Logging` provides structured lifecycle logging for applications and
connector workflows. `ConnectorFabric` caches and coordinates vendor connectors
while sharing input loading, logging, data normalization, retry behavior, and
serialization.

## Connector Fabric

Use specialized helpers when they match the operation:

```python
from extended_data import ConnectorFabric

fabric = ConnectorFabric(inputs={"ZOOM_ACCOUNT_ID": "..."}, from_environment=False)
zoom = fabric.get_zoom_client(client_id="...", client_secret="...")
```

Use the registry-backed generic path when a connector is registered by name:

```python
github = fabric.get_connector(
    "github",
    github_owner="jbcom",
    github_token="...",
)
```

Both paths share the same input provider and lifecycle logger, and both cache
instances by connector type and constructor inputs. Generic connector names are
stripped and lowercased before lookup.

Connectors that inherit `VendorConnectorBase` can keep raw transport access with
`request()` or use `request_data()`, `get_data()`, `post_data()`, and the other
verb-specific helpers to decode HTTP JSON, YAML, TOML, HCL, or text responses
through the same Tier 2 container bridge used by file and input decoding.

Use the catalog helpers when a workflow needs to inspect which integrations can
run in the current environment:

```python
catalog = fabric.list_connector_info()
github_info = fabric.get_connector_info("github")
```

Each catalog entry includes availability, source, extra name, install command,
required packages, missing packages, module, class, and description fields.

## Optional Integrations

Install only the vendor or AI layers you need:

```bash
pip install "extended-data[aws,github,vault]"
pip install "extended-data[google,slack,zoom]"
pip install "extended-data[ai]"        # LangChain, MCP, and Strands
pip install "extended-data[meshy,mcp]"
```

CrewAI tool adapters are still importable when users install `crewai` directly,
but `extended-data` does not expose a CrewAI extra while current CrewAI
dependency trees pull vulnerable `chromadb` releases.
All built-in CrewAI tool adapters use
`extended_data.connectors._optional.get_crewai_tool_decorator()` so missing or
incompatible CrewAI installs fail with the same user-managed install guidance.

Optional dependency checks live in `extended_data.connectors._optional`; there
are no old package compatibility shims in the public API. When a known built-in
connector is requested without its optional extra installed, the registry raises
an `ImportError` with the exact `extended-data[...]` install target instead of
reporting the connector as unknown.
