# Package Surface

`extended-data` is one Python distribution with a single `extended_data`
namespace. The root package exposes the primitives and adapters users need most
often.
The old `extended_data_types`, `lifecyclelogging`,
`directed_inputs_class`, and `vendor_connectors` import namespaces are not
preserved in this major version.

```python
from extended_data import (
    ConnectorFabric,
    DataDecodeError,
    DataWorkflow,
    ExtendedDict,
    ExtendedList,
    ExtendedSet,
    ExtendedString,
    ExtendedTuple,
    GitHubConnector,
    GoogleConnector,
    InputProvider,
    Logging,
    SecretsConnector,
    SlackConnector,
    SyncOptions,
    decode_json,
    extend_data,
    encode_yaml,
    flatten_map,
    normalize_data_encoding,
    number_to_words,
    to_builtin,
)
```

## Tiers

- Tier 1 `extended_data.primitives` modules are pure functions and codecs for
  strings, numbers, maps, lists, matching, state, type coercion, and structured
  formats.
- Tier 2 `extended_data.containers` classes wrap Python container primitives as
  `ExtendedString`, `ExtendedDict`, `ExtendedList`, `ExtendedTuple`, and
  `ExtendedSet` with
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
aliases = ExtendedTuple(("api", ("gateway",))).flatten()
tags = ExtendedSet({"prod", "prod", ""}).compact()
words = number_to_words(42)
encoding = normalize_data_encoding("YML")
```

`ExtendedDict`, `ExtendedList`, `ExtendedTuple`, and `ExtendedSet` recursively
promote nested plain values on construction and mutation, so method chains can
continue through data loaded from normal Python literals:

```python
payload = ExtendedDict({"service": {"name": "api"}})
payload["service"]["name"].upper_first()
```

Mutation and common operator paths are part of that contract: `setdefault()`,
in-place dict merge, list in-place concatenation, list in-place repetition,
tuple slicing, tuple concatenation, and tuple repetition preserve Tier 2
containers instead of leaking plain nested values.

Container methods that return derived collections stay in Tier 2 as well:
`ExtendedDict.filter()` returns an `ExtendedTuple` of accepted and rejected
`ExtendedDict` values, and `ExtendedDict.all_values()` returns an
`ExtendedList`.

Tier 3 decode surfaces promote decoded values into Tier 2 containers by
default:

```python
from extended_data import decode_file

payload = decode_file('{"service": {"name": "api"}}', suffix="json")
assert payload["service"]["name"].upper_first() == "Api"
```

Pass `as_extended=False` when a decode boundary should return standard Python
containers. Use `extend_data(value)` to promote existing plain data and
`to_builtin(value)` to lower extended containers back to standard Python data.
Tuple values are promoted to `ExtendedTuple` and lowered back to Python tuples,
so the Tier 2 surface does not silently turn immutable input data into mutable
lists.
Format encoders lower Tier 2 containers the same way before serializing JSON,
YAML, TOML, and HCL output.

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
payloads. Active, frozen, shifted, and merged input snapshots are `ExtendedDict`
values, and input decorator metadata/options are promoted the same way. The old
case-insensitive input mapping is intentionally not preserved; exact keys keep
configuration wiring explicit while still letting direct snapshots use Tier 2
methods. Use `snapshot_inputs()` for a detached promoted copy of active or
frozen state, and `replace_inputs()` when a workflow should install a new
active snapshot instead of mutating `.inputs` directly.

```python
inputs = InputProvider(inputs={"service": {"name": "api"}}, from_environment=False)
assert inputs.inputs["service"]["name"].upper_first() == "Api"
assert isinstance(inputs.merge_inputs({"service": {"region": "us-east-1"}}), ExtendedDict)
assert inputs.snapshot_inputs()["service"]["region"].upper_first() == "Us-east-1"
```

`get_input()` is the scalar coercion boundary for booleans, numbers, paths,
datetimes, and credential strings. Pass `as_extended=True` when a raw injected
input value should remain in Tier 2 form.

`Logging` provides structured lifecycle logging for applications and connector
workflows without creating log files unless file output is explicitly enabled.
Stored log message collections are exposed as `ExtendedDict` values keyed by
storage marker, with each marker containing an `ExtendedSet` of promoted
messages.

`ConnectorFabric` caches and coordinates vendor connectors while sharing input
loading, logging, data normalization, retry behavior, and serialization.

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

Every built-in connector class registered by name is also exported from
`extended_data` and `extended_data.connectors`. Those exports are real classes,
not `None` sentinels. Vendor SDKs load when connector instances need them, so
package import remains lightweight while missing optional extras still fail at
the operation boundary with install guidance.

Connectors that inherit `VendorConnectorBase` can keep raw transport access with
`request()` or use `request_data()`, `get_data()`, `post_data()`, and the other
verb-specific helpers to decode HTTP JSON, YAML, TOML, HCL, or text responses
through the same Tier 2 container bridge used by file and input decoding.
Connector methods that return vendor data payloads should call
`extend_result()` at the return boundary, making SDK-shaped dictionaries,
lists, decoded repository files, GraphQL results, and workflow-builder output
first-class `ExtendedDict`, `ExtendedList`, `ExtendedTuple`, and
`ExtendedString` values. This is an intentional major-version break from plain
`dict`/`list` payloads; use `to_builtin()` at serialization, CLI, MCP, or SDK
handoff boundaries.
Data-returning AI tool wrapper functions follow the same contract and annotate
their payload returns as `ExtendedDict` or `ExtendedList[ExtendedDict]`.
LangChain, CrewAI, Strands, and auto-detection factory functions still return
plain framework tool object lists.

```python
payload = github.get_repository_file("service.json")
assert payload["service"]["name"].upper_first() == "Api"
```

The `secrets` adapter is the Python-facing bridge to the standalone
`secretsync` project. It uses native bindings when present and otherwise falls
back to the CLI, which must emit the stable `secretsync pipeline --output json`
result envelope for both dry-run and apply runs.
Secrets tool factories are exported from `extended_data.secrets`; the duplicate
`extended_data.secrets.tools` module path is intentionally not preserved.

```python
from extended_data import SecretsConnector, SyncOptions

result = SecretsConnector(prefer_native=False).run_pipeline(
    "pipeline.yaml",
    SyncOptions(dry_run=True),
)
```

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
reporting the connector as unknown. Built-in connectors must also be registered
through the `extended_data.connectors` entry point group; missing entry-point
registration is treated as a package configuration error instead of being
patched over by direct source imports.
