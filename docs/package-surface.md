# Package Surface

`extended-data` is one Python distribution with a single `extended_data`
namespace. The root package exposes the primitives users need most often:

```python
from extended_data import (
    ConnectorFabric,
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

```python
name = ExtendedString("API Response Value").to_snake_case()
payload = ExtendedDict({"outer": {"inner": 1}}).flatten()
items = ExtendedList([1, [2, [3]]]).flatten()
tags = ExtendedSet({"prod", "prod", ""}).compact()
```

Tier 3 decode surfaces can promote plain decoded values into Tier 2 containers:

```python
from extended_data import decode_file

payload = decode_file('{"service": {"name": "api"}}', suffix="json", as_extended=True)
assert payload["service"]["name"].upper_first() == "Api"
```

Use `extend_data(value)` to promote existing plain data and `to_builtin(value)`
to lower extended containers back to standard Python data.

`InputProvider` loads input data from explicit mappings, environment variables,
and stdin, then decodes or coerces values through the primitive layer. Its
`decode_input(..., as_extended=True)` path gives input-driven workflows the same
container bridge as file and Base64 decoding. `Logging` provides structured
lifecycle logging for applications and connector workflows. `ConnectorFabric`
caches and coordinates vendor connectors while sharing input loading, logging,
data normalization, retry behavior, and serialization.

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
pip install "extended-data[ai]"
pip install "extended-data[meshy,mcp]"
```

Optional dependency checks live in `extended_data.connectors._optional`; there
are no old package compatibility shims in the public API. When a known built-in
connector is requested without its optional extra installed, the registry raises
an `ImportError` with the exact `extended-data[...]` install target instead of
reporting the connector as unknown.
