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
  `ExtendedSet` with ergonomic methods over Tier 1 primitives. They use
  `UserString`, `UserDict`, `UserList`, immutable `tuple`, or
  `MutableSet`-compatible bases depending on the underlying data shape.
- Tier 3 processors use the first two tiers to handle files, imports, exports,
  inputs, API data, vendor integrations, and workflows.

Clean major-version primitive names prefer explicit Python words over inherited
helper spellings: use `bytes_to_string()` and the `string_to_*()` conversion
family (`string_to_bool()`, `string_to_int()`, `string_to_float()`,
`string_to_path()`, `string_to_date()`, `string_to_datetime()`, and
`string_to_time()`). The old `bytestostr` and `strto*` helper names are
intentionally not preserved.
Tier 1 public exports stay function-oriented; use `get_default_dict()` when a
workflow needs nested or sorted default mappings rather than importing the
internal sorted-default mapping helper class.

Direct JSON, YAML, TOML, and HCL decode failures raise `DataDecodeError` with
format and position context while preserving the parser exception as the cause;
the public error message does not echo the raw payload.

```python
name = ExtendedString("API Response Value").to_snake_case()
payload = ExtendedDict({"outer": {"inner": 1}}).flatten()
items = ExtendedList([1, [2, [3]]]).flatten()
services = ExtendedList(["api", "worker", "db"]).filter_values(allowlist=["api", "worker"])
typed_items = ExtendedList(["api", 2, True]).split_by_type(primitive_only=True)
typed_aliases = ExtendedTuple(("api", 2, True)).split_by_type(primitive_only=True)
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
containers instead of leaking plain nested values. `ExtendedSet` named
mutators such as `update()`, `intersection_update()`, `difference_update()`,
and `symmetric_difference_update()` preserve promoted values as well.
String tokenization and partitioning paths are covered too:
`ExtendedString.split()`, `rsplit()`, and `splitlines()` return `ExtendedList`
values containing `ExtendedString` parts, while `partition()` and
`rpartition()` return `ExtendedTuple` values. String formatting paths
`format()` and `format_map()` return `ExtendedString`.

Container methods that return derived collections stay in Tier 2 as well:
`ExtendedDict.filter()` returns an `ExtendedTuple` of accepted and rejected
`ExtendedDict` values, and `ExtendedDict.all_values()` returns an
`ExtendedList`. `ExtendedList.split_by_type()`,
`ExtendedTuple.split_by_type()`, and `ExtendedDict.split_by_type()` expose the
Tier 1 split helpers as type-name keyed `ExtendedDict` results; tuple inputs
keep tuple-shaped grouped values.
Generic type routing can still ask for plain data roles:
`typeof(value, primitive_only=True)` reports Extended strings, lists, tuples,
mappings, and sets as `str`, `list`, `list`, `dict`, and `set`.

Tier 3 file and decode surfaces promote decoded values into Tier 2 containers
by default:

```python
from extended_data import decode_file, read_data_file

payload = decode_file('{"service": {"name": "api"}}', suffix="json")
file_payload = read_data_file("config/service.json")
assert payload["service"]["name"].upper_first() == "Api"
assert file_payload["service"]["name"].upper_first() == "Api"
```

Pass `as_extended=False` when a decode boundary should return standard Python
containers. Use `extend_data(value)` to promote existing plain data and
`to_builtin(value)` to lower extended containers back to standard Python data.
Tuple values are promoted to `ExtendedTuple` and lowered back to Python tuples,
so the Tier 2 surface does not silently turn immutable input data into mutable
lists.
Format encoders lower Tier 2 containers the same way before serializing JSON,
YAML, TOML, and HCL output, including extended mapping keys that must become
plain strings before JSON handoff.

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
`AWSConnector` and `GoogleConnector` are unified connector classes in this
major version: common S3, Organizations, SSO, Workspace, Cloud Resource
Manager, Billing, and service-discovery operations live directly on those
connectors. The old split between base connector classes and separate `*Full`
connector classes is intentionally not preserved.
The Google registry surface is unified too: `google` is the first-class
connector name for Workspace, Cloud Resource Manager, Billing, and service
discovery operations. Split `google_cloud`, `google_workspace`, and
`google_billing` connector aliases are intentionally not preserved.
AWS Secrets Manager prefix loading is generic too: use
`AWSConnector.load_secrets_by_prefix()` when a workflow needs a promoted mapping
of secret names to values. The old vendor-specific ASM loader name is
intentionally not preserved.
AWS secret listing/deletion and Vault role filtering use the canonical `prefix`
keyword. The old `name_prefix` convenience keyword is intentionally not
preserved.

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
The generic CLI `call` command and MCP bridge expose only connector methods
that advertise Extended Data payload returns, so raw SDK client factories and
low-level HTTP helpers do not leak into serialized tool catalogs.
Those serialized boundaries apply redaction after Tier 2 containers are lowered
to JSON-compatible data. Common secret-bearing keys such as `password`,
`api_key`, `access_token`, `authorization`, and `client_secret`, plus token-like
strings in error text, are replaced with `[REDACTED]` before CLI stdout/stderr
or MCP tool responses are emitted.
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
names = fabric.list_connectors()
catalog = fabric.list_connector_info()
github_info = fabric.get_connector_info("github")
```

`list_connectors()` returns an `ExtendedList` of available connector names.
Each catalog entry includes availability, source, extra name, install command,
required packages, missing packages, module, class, and description fields.
The installed CLI exposes the same discovery layer for shell automation:

```bash
extended-data list --json
extended-data info github --json
extended-data methods github --json
```

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
are no old package compatibility shims in the public API. Missing old imports
are intentional in this major version so unfinished migration work stays
visible. When a known built-in connector is requested without its optional extra
installed, the registry raises an `ImportError` with the exact
`extended-data[...]` install target instead of reporting the connector as
unknown. Built-in connectors must also be registered through the
`extended_data.connectors` entry point group; missing entry-point registration is
treated as a package configuration error instead of being patched over by direct
source imports.
