# Package Surface

`extended-data` is one Python distribution with a single `extended_data`
namespace. The root package exposes first-class containers, Tier 3 processors,
and integrated connectors; pure Tier 1 utilities are imported from
`extended_data.primitives`.
The old `extended_data_types`, `lifecyclelogging`,
`directed_inputs_class`, and `vendor_connectors` import namespaces are not
preserved in this major version.

```python
from extended_data import (
    ConnectorFabric,
    DataDecodeError,
    DataFile,
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
    list_data_transform_steps,
    extend_data,
    to_builtin,
)
from extended_data.primitives import (
    decode_json,
    encode_yaml,
    normalize_data_encoding,
    number_to_words,
    redact_sensitive_text,
)
```

## Tiers

- Tier 1 `extended_data.primitives` modules are pure functions and codecs for
  strings, numbers, maps, lists, matching, state, redaction, type coercion, and
  structured formats.
- Tier 2 `extended_data.containers` classes wrap Python container primitives as
  `ExtendedString`, `ExtendedDict`, `ExtendedList`, `ExtendedTuple`, and
  `ExtendedSet` with ergonomic methods over Tier 1 primitives. They use
  `UserString`, `UserDict`, `UserList`, immutable `tuple`, or
  `MutableSet`-compatible bases depending on the underlying data shape.
- Tier 3 processors use the first two tiers to handle files, imports, exports,
  inputs, API data, external integrations, and workflows.

Clean major-version primitive names, including JSON/YAML/TOML/HCL codecs, live
under `extended_data.primitives` and prefer explicit Python words over
inherited helper spellings: use `bytes_to_string()` and the `string_to_*()`
conversion family (`string_to_bool()`, `string_to_int()`, `string_to_float()`,
`string_to_path()`, `string_to_date()`, `string_to_datetime()`, and
`string_to_time()`). The old `bytestostr` and `strto*` helper names are
intentionally not preserved, and pure utility functions are not re-exported
from the package root.
Tier 1 public exports stay function-oriented; use `get_default_dict()` when a
workflow needs nested or sorted default mappings rather than importing the
internal sorted-default mapping helper class.
Use `redact_sensitive_text()` and `redact_sensitive_data()` when diagnostics or
JSON-like payloads need common secret-bearing keys and token-shaped strings
removed before display. Pass `values=[...]` when a caller knows additional
context-specific identifiers, such as emails, paths, URLs, or external resource
IDs, must be withheld as well; URL-encoded forms of those values are redacted
too.

Direct JSON, YAML, TOML, and HCL primitive decode failures raise
`DataDecodeError` with format and position context while preserving the parser
exception as the cause; the public error message does not echo the raw payload.

```python
name = ExtendedString("API Response Value").to_snake_case()
matched = ExtendedString("api-gateway").is_partial_match("gateway")
payload = ExtendedDict({"outer": {"inner": 1}}).flatten()
items = ExtendedList([1, [2, [3]]]).flatten()
services = ExtendedList(["api", "worker", "db"]).filter_values(allowlist=["api", "worker"])
typed_items = ExtendedList(["api", 2, True]).split_by_type(primitive_only=True)
typed_aliases = ExtendedTuple(("api", 2, True)).split_by_type(primitive_only=True)
aliases = ExtendedTuple(("api", ("gateway",))).flatten()
tags = ExtendedSet({"prod", "prod", ""}).compact()
words = number_to_words(42)
encoding = normalize_data_encoding("YML")
safe_error = redact_sensitive_text(
    "failed for user@example.com and user%40example.com",
    values=["user@example.com"],
)
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
`format()` and `format_map()` return `ExtendedString`. String matching paths
`is_partial_match()` and `is_non_empty_match()` expose the Tier 1 matching
helpers through `ExtendedString`. Scalar conversion paths `to_bool()`,
`to_int()`, `to_float()`, `to_path()`, `to_date()`, `to_datetime()`, and
`to_time()` expose the Tier 1 `string_to_*()` family directly on
`ExtendedString`. Structured text paths `decode_json()`, `decode_yaml()`,
`decode_toml()`, `decode_hcl2()`, and `decode_base64()` decode from the string
container and promote decoded maps/lists into Tier 2 data by default.
`ExtendedString.reconstruct_special_type()` and container
`reconstruct_special_types()` methods restore booleans, numbers, paths, dates,
times, and structured JSON/YAML values while keeping reconstructed collections
inside Tier 2 containers. Container `to_export_safe()` and `wrap_for_export()`
methods expose the Tier 3 export boundary directly from promoted values for
JSON, YAML, TOML, HCL, and raw string output.

Container methods that return derived collections stay in Tier 2 as well:
`ExtendedDict.filter()` returns an `ExtendedTuple` of accepted and rejected
`ExtendedDict` values, and `ExtendedDict.all_values()` returns an
`ExtendedList`. `ExtendedList.split_by_type()`,
`ExtendedTuple.split_by_type()`, and `ExtendedDict.split_by_type()` expose the
Tier 1 split helpers as type-name keyed `ExtendedDict` results; tuple inputs
keep tuple-shaped grouped values. `ExtendedList.first_non_empty()` and
`ExtendedTuple.first_non_empty()` return the first ordered non-empty value
without lowering promoted nested data. `ExtendedList.zipmap()` and
`ExtendedTuple.zipmap()` return promoted `ExtendedDict` mappings from ordered
key containers and value iterables. `ExtendedDict.first_non_empty_value()`
returns promoted Tier 2 values when it selects nested maps, lists, tuples, sets,
or strings. `ExtendedDict.first_non_empty_entry()` and
`ExtendedDict.non_empty_entries()` return promoted keyed entries for workflows
that need to preserve the selected key context.
Generic type routing can still ask for plain data roles:
`typeof(value, primitive_only=True)` reports Extended strings, lists, tuples,
mappings, and sets as `str`, `list`, `list`, `dict`, and `set`.

Tier 3 file and decode surfaces promote decoded values into Tier 2 containers
by default:

```python
from extended_data import DataFile, decode_file, read_data_file

payload = decode_file('{"service": {"name": "api"}}', suffix="json")
file_payload = read_data_file("config/service.json")
artifact = DataFile.decode('{"service": {"name": "api"}}', suffix="json")
assert payload["service"]["name"].upper_first() == "Api"
assert file_payload["service"]["name"].upper_first() == "Api"
assert artifact.metadata["encoding"].upper_first() == "Json"
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

`DataFile` is the Tier 3 artifact surface for one decoded file, URL, or
in-memory payload. It keeps `source`, `encoding`, and source metadata promoted,
returns decoded `data` as Tier 2 containers by default, exposes detached
`as_extended()` views, writes output artifacts through the same export boundary
as `write_file()`, and starts artifact-first processing with `workflow()`.
Source labels and metadata are redacted with the Tier 1 redaction policy before
they enter workflow step names or `WorkflowResult.metadata`; caller-supplied
metadata cannot override the sanitized core `source` and `path` fields.

`DataWorkflow` is the Tier 3 composition surface for higher-order data
processing. It reads or decodes structured data through the file and format
processors, accepts `DataFile` artifacts with `from_data_file()`, promotes
values into Tier 2 containers by default, deep-merges in-memory or file-backed
mapping layers, applies reusable `WorkflowStep` functions or named transform
steps, writes output artifacts, and returns a `WorkflowResult` with the
completed value, output path, step trail, and promoted metadata.
`DataWorkflow.merge()` deep-merges mapping values through the Tier 2
`ExtendedDict` primitive, and `merge_file()` decodes structured file layers
through `DataFile` before merging. `DataWorkflow.transform()` applies the same
named Tier 2
transform catalog exposed by the CLI, including `reconstruct`, `unhump`,
`deduplicate`, `compact`, and string case transforms. Workflow metadata is
preserved across `then()`, `run()`, `merge()`, `merge_file()`, `transform()`, `as_builtin()`,
`as_extended()`, and `write()`, so file and API provenance from `DataFile`
artifacts remains attached to the result. `WorkflowResult.as_extended()` returns
a detached promoted view of the completed value, and result-level
`to_export_safe()` / `wrap_for_export()` expose the same export boundary used by
Tier 2 containers.

```python
from extended_data import DataWorkflow

env_data = DataWorkflow.from_file("config/dev.yaml").value
result = (
    DataWorkflow.from_file("config/base.yaml")
    .merge(env_data, name="merge-env")
    .transform("reconstruct", "unhump")
    .write("build/config.yaml")
)

assert result.steps == (
    "read:config/base.yaml",
    "merge-env",
    "transform:reconstruct",
    "transform:unhump",
    "write:build/config.yaml",
)
assert result.metadata["source"] == "config/base.yaml"
assert result.as_extended()["service"]["name"].upper_first() == "Api"
assert result.to_export_safe()["service"]["name"] == "api"
assert "unhump" in list_data_transform_steps()
```

Missing workflow input files raise `FileNotFoundError`, and empty workflow
writes raise `ValueError` unless `allow_empty=True` is passed. Missing merge
layers, unknown transform names, and operations that do not match the current
data shape raise instead of silently preserving stale workflow state.

`InputProvider` loads input data from explicit mappings, environment variables,
and stdin, then decodes or coerces values through the shared primitive and
file/data layers. Stdin JSON and JSON/YAML `decode_input()` paths use the same
structured decoder boundary as file and connector payloads. Its
`decode_input(..., as_extended=True)` path gives input-driven workflows the same
container bridge as file and Base64 decoding; fallback values use that same
promotion rule, so defaults do not silently drop back to plain dictionaries.
Requested input coercions are strict, and diagnostics identify the input key and
failed operation without echoing raw values from environment variables, stdin,
JSON, YAML, or Base64 payloads. Active, frozen, shifted, and merged input
snapshots are `ExtendedDict` values, and input decorator metadata/options are
promoted the same way. The old case-insensitive input mapping is intentionally
not preserved; exact keys keep configuration wiring explicit while still
letting direct snapshots use Tier 2 methods. Use `snapshot_inputs()` for a
detached promoted copy of active or frozen state, and `replace_inputs()` when a
workflow should install a new active snapshot instead of mutating `.inputs`
directly.

```python
inputs = InputProvider(inputs={"service": {"name": "api"}}, from_environment=False)
assert inputs.inputs["service"]["name"].upper_first() == "Api"
assert isinstance(inputs.merge_inputs({"service": {"region": "us-east-1"}}), ExtendedDict)
assert inputs.snapshot_inputs()["service"]["region"].upper_first() == "Us-east-1"
fallback = inputs.decode_input("missing", default={"enabled": "true"}, as_extended=True)
assert fallback.reconstruct_special_types()["enabled"] is True
```

`get_input()` is the scalar coercion boundary for booleans, numbers, paths,
datetimes, and credential strings. Pass `as_extended=True` when a raw injected
input value should remain in Tier 2 form.

`Logging` provides structured lifecycle logging for applications and connector
workflows without creating log files unless file output is explicitly enabled.
Stored log message collections are exposed as `ExtendedDict` values keyed by
storage marker, with each marker containing an `ExtendedSet` of promoted
messages. `get_stored_messages()` returns a detached promoted message set for
one marker, and `snapshot_stored_messages()` returns a detached `ExtendedDict`
copy of all stored collections for downstream export or workflow composition.
Runtime log messages and attached JSON payloads are redacted with the Tier 1
redaction primitives before they reach Python logging handlers or stored message
collections. `exit_run()` formatting failures also report a redacted result
snapshot and suppress the internal formatting exception chain so diagnostics do
not echo raw payload data.

`ConnectorFabric` caches and coordinates registered connectors while sharing input
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
of secret names to values. The old service-specific ASM loader name is
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
not `None` sentinels. Optional SDKs load when connector instances need them, so
package import remains lightweight while missing optional extras still fail at
the operation boundary with install guidance. `list_connectors()` reports the
complete connector catalog, including known connectors whose optional SDK extras
are not installed; use `list_available_connectors()` for only connectors whose
runtime requirements are installed. Use `list_connector_info()` when tooling
needs the complete catalog plus missing dependency and install guidance.
Catalog entries include normalized categories and capabilities;
`list_connector_categories()`,
`list_connector_capabilities()`, `list_connectors_by_category()`, and
`list_connectors_by_capability()` let workflows select integrations by data
domain or supported operation without parsing class names. `ConnectorFabric`
hashes secret-like cache-key fields such as `token`, `api_key`, `password`, and
`client_secret` before storing cache entries, so cache inspection and debug
output do not expose raw credential material.
Custom `ConnectorBase` subclasses can set `CONNECTOR_CATEGORY` and
`CONNECTOR_CAPABILITIES` so entry-point connectors participate in the same
catalog query surface.

Connectors that inherit `ConnectorBase` can keep raw transport access with
`request()` or use `request_data()`, `get_data()`, `post_data()`, and the other
verb-specific helpers to decode HTTP JSON, YAML, TOML, HCL, or text responses
through the same Tier 2 container bridge used by file and input decoding.
Built-in connectors that parse HTTP JSON responses should decode response bytes
through these shared data primitives and lower to built-in values only at model
validation or redaction boundaries. Use
`request_data_file()` when an API workflow needs the decoded data plus
non-secret response provenance such as source URL, HTTP status, content type,
method, and endpoint in a `DataFile` artifact. Use `request_workflow()` when
that response should immediately become a `DataWorkflow` with the same promoted
metadata, named transforms, merge helpers, and export/write boundary.
Connector methods that return external data payloads should call
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
The MCP bridge also publishes credential-free catalog tools:
`extended_data_list_connectors`, `extended_data_list_available_connectors`,
`extended_data_list_connector_info`, `extended_data_get_connector_info`,
`extended_data_list_connector_categories`, `extended_data_list_connector_capabilities`,
`extended_data_list_connectors_by_category`, and
`extended_data_list_connectors_by_capability`.
CLI `--arg` values that look like JSON are decoded through the shared
structured data boundary before method dispatch, matching file, input, and
connector payload decoding.
Google service-account strings and Meshy persisted manifests/metadata use that
same boundary, so connector-local reads do not grow private JSON parsers.
AWS S3 JSON object writes and Meshy manifest writes go through the shared export
boundary, so connector persistence uses the same Tier 3 data-file encoding path;
Meshy vector-store metadata follows the same path.
CLI JSON output, MCP tool results, and SecretSync `results_json` are exported
through the same path after redaction.
GitHub workflow YAML generation and `Logging.exit_run()` stdout serialization
also route through the shared exporter.
Serialized CLI/MCP boundaries apply Tier 1 redaction after Tier 2 containers
are lowered to JSON-compatible data, and connector API error messages use the
same redaction policy before exceptions are raised. Common secret-bearing keys
such as `password`, `api_key`, `access_token`, `authorization`, and
`client_secret`, plus token-like strings in error text, are replaced with
`[REDACTED]` before CLI stdout/stderr, MCP tool responses, or raised transport
errors expose them. CLI and MCP connector calls pass method arguments through
`values=[...]` as context-specific diagnostic data, and connectors can add their
own operation-specific values for resource IDs, paths, URLs, emails, prompt
text, or external payload handles that are sensitive only in that operation.
LangChain, CrewAI, Strands, and auto-detection factory functions still return
plain framework tool object lists.

```python
payload = github.get_repository_file("service.json")
assert payload["service"]["name"].upper_first() == "Api"
```

The `secrets` connector is the Python-facing bridge to the standalone SecretSync
project (`jbcom/secrets-sync`). It uses the `secretsync` CLI, which must emit
the stable `secretsync pipeline --output json` result envelope for both dry-run
and apply runs. The connector decodes that envelope through the shared file/data
primitives before lowering it into the `SyncResult` model. Configuration
inspection reads YAML configs through the same decoded `DataFile` artifact path.
Secrets tool factories are exported from `extended_data.secrets`; the duplicate
`extended_data.secrets.tools` module path is intentionally not preserved.

```python
from extended_data import SecretsConnector, SyncOptions

result = SecretsConnector().run_pipeline(
    "pipeline.yaml",
    SyncOptions(dry_run=True),
)
```

Use the catalog helpers when a workflow needs to inspect known integrations and
which ones can run in the current environment:

```python
names = fabric.list_connectors()
available = fabric.list_available_connectors()
catalog = fabric.list_connector_info()
github_info = fabric.get_connector_info("github")
cloud_connectors = fabric.list_connectors_by_category("cloud")
repository_connectors = fabric.list_connectors_by_capability("repositories")
```

`list_connectors()` returns an `ExtendedList` of catalog connector names.
`list_available_connectors()` returns the subset runnable in the current
environment. Each catalog entry includes availability, source, category,
capabilities, extra name, install command, required packages, missing packages,
module, class, and description fields.
The installed CLI exposes the same discovery layer for shell automation:

```bash
extended-data decode '{"service": {"name": "api"}}' --suffix json
extended-data decode --file config.yaml --output json
extended-data inspect --file config.yaml
extended-data merge config/base.yaml config/dev.yaml --output yaml
extended-data transform --file payload.json --step reconstruct --step unhump
extended-data list --json
extended-data list --category cloud
extended-data list --capability repositories --json
extended-data info github --json
extended-data methods github --json
```

The `extended-data` console script is the package-level CLI. Data commands use
`DataFile`, `DataWorkflow`, and the shared export boundary directly; connector
commands are delegated to the connector CLI so existing catalog, method, call,
and MCP workflows stay on the same entrypoint.

## Optional Integrations

Install only the external service or AI layers you need:

```bash
pip install "extended-data[aws,github,vault]"
pip install "extended-data[google,slack,zoom]"
pip install "extended-data[anthropic,cursor]"
pip install "extended-data[ai]"        # LangChain, MCP, and Strands
pip install "extended-data[langchain,mcp,strands]"
pip install "extended-data[meshy,mcp]"
pip install "extended-data[meshy,vector,webhooks]"
```

Published runtime extras:

| Extra | Purpose |
| --- | --- |
| `extended-data[anthropic]` | Anthropic API connector and tools |
| `extended-data[aws]` | AWS connector operations |
| `extended-data[cursor]` | Cursor connector helpers |
| `extended-data[github]` | GitHub connector operations |
| `extended-data[google]` | Google Workspace, Cloud, Billing, and services |
| `extended-data[langchain]` | LangChain tool adapters |
| `extended-data[mcp]` | MCP server bridge |
| `extended-data[meshy]` | Meshy 3D asset connector |
| `extended-data[secrets]` | SecretSync Python bridge dependencies |
| `extended-data[slack]` | Slack connector operations |
| `extended-data[strands]` | Strands tool adapters |
| `extended-data[vault]` | Vault connector operations |
| `extended-data[vector]` | Local vector search for generated asset metadata |
| `extended-data[webhooks]` | Webhook listener support |
| `extended-data[zoom]` | Zoom connector operations |
| `extended-data[ai]` | Aggregate LangChain, MCP, and Strands install target |

CrewAI tool adapters are still importable when users install `crewai` directly,
but `extended-data` does not expose a CrewAI extra while current CrewAI
dependency trees pull vulnerable `chromadb` releases.
All built-in CrewAI tool adapters use
`extended_data.connectors._optional.get_crewai_tool_decorator()` so missing or
incompatible CrewAI installs fail with the same user-managed install guidance.

Optional dependency checks live in `extended_data.connectors._optional`; there
are no old package compatibility shims in the public API. Missing old imports
are intentional in this major version so incorrect callers fail loudly. When a
known built-in connector is requested without its optional extra
installed, the registry raises an `ImportError` with the exact
`extended-data[...]` install target instead of reporting the connector as
unknown. Built-in connectors must also be registered through the
`extended_data.connectors` entry point group; missing entry-point registration is
treated as a package configuration error instead of being patched over by direct
source imports.
