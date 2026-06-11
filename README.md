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
pip install "extended-data[anthropic,cursor]"
pip install "extended-data[ai]"        # LangChain, MCP, and Strands
pip install "extended-data[langchain,mcp,strands]"
pip install "extended-data[meshy,mcp]"
pip install "extended-data[meshy,vector,webhooks]"
pip install "extended-data[secrets]"
```

Published runtime extras are `anthropic`, `aws`, `cursor`, `github`, `google`,
`langchain`, `mcp`, `meshy`, `secrets`, `slack`, `strands`, `vault`, `vector`,
`webhooks`, `zoom`, and aggregate `ai`.

CrewAI adapters remain available when `crewai` is installed independently, but
`extended-data` intentionally does not publish a CrewAI extra while current
CrewAI releases pull vulnerable `chromadb` versions transitively.

## Usage

```python
from extended_data import ConnectorFabric, DataFile, DataWorkflow, ExtendedDict, InputProvider, Logging, decode_file
from extended_data.primitives import decode_json, encode_yaml, number_to_words, redact_sensitive_text

logger = Logging(logger_name="example")
inputs = InputProvider(inputs={"GITHUB_OWNER": "jbcom"}, from_environment=False)
connectors = ConnectorFabric(inputs=inputs.inputs, logger=logger)
data = decode_json('{"status": "ok"}')
payload = ExtendedDict(data).deep_merge({"source": "example"})
decoded_file = decode_file('{"service": {"name": "api"}}', suffix="json")
artifact = DataFile.decode('{"service": {"name": "api"}}', suffix="json")
workflow = DataWorkflow.from_value(payload).then(("normalize", lambda data: data.unhump())).result()

print(encode_yaml(payload))
print(decoded_file["service"]["name"].upper_first())
print(number_to_words(42))
print(redact_sensitive_text("Authorization: Bearer raw_token"))
print(redact_sensitive_text("failed for user@example.com", values=["user@example.com"]))
print(artifact.metadata["encoding"])
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

Built-in connector classes are also package-root exports when direct
construction reads better:

```python
from extended_data import GitHubConnector, SlackConnector
```

Connector names are normalized before lookup. If a known built-in connector is
requested without its optional extra installed, the registry raises an
`ImportError` with the matching `extended-data[...]` install target.

Inspect connector availability before wiring vendor workflows:

```python
names = connectors.list_connectors()
catalog = connectors.list_connector_info()
github_info = connectors.get_connector_info("github")
```

`list_connectors()` returns an `ExtendedList` of available connector names.
Use `list_connector_info()` when a workflow needs availability, extra, install,
class, module, and description metadata.

The same catalog is available from the CLI:

```bash
extended-data list
extended-data info github --json
extended-data methods github --json
```

## Package Shape

```text
extended_data/
  primitives/   Tier 1 pure functions and codecs
  containers/   Tier 2 ExtendedString/Dict/List/Tuple/Set wrappers
  io/           Tier 3 file, import, export, and base64 processors
  inputs/       InputProvider and decorator-based input injection
  logging/      structured lifecycle logging
  connectors/   Tier 3 ConnectorFabric and vendor adapters
  secrets/      SecretSync CLI bridge and typed result exports
  workflows/    Tier 3 higher-order workflow composition
```

Tier 1 primitive names are explicit in this major version and live under
`extended_data.primitives`, not the package root. Use
`bytes_to_string()` for bytes-like coercion and `string_to_bool()`,
`string_to_int()`, `string_to_float()`, `string_to_path()`,
`string_to_date()`, `string_to_datetime()`, and `string_to_time()` for scalar
string conversion. Use `redact_sensitive_text()` and
`redact_sensitive_data()` for diagnostic and JSON-like payload redaction. Pass
`values=[...]` when a caller knows specific context values, such as resource
IDs, emails, paths, or URLs, must be withheld in addition to common secret
fields. The old `bytestostr` and `strto*` helper names are not preserved. Old
package import namespaces are not shimmed; missing imports are intentional so
remaining migration work fails fast.
Tier 1 public exports stay function-oriented; use `get_default_dict()` for
nested or sorted default mappings instead of importing the internal helper class.

Vendor connectors are first-class adapters in the data fabric. `ConnectorFabric`
uses the registry to resolve connectors by name, injects shared input/logging
context, caches connector instances, and lets specialized helpers coexist with
generic vendor lookup. `list_connectors()` returns registered connectors whose
runtime requirements are installed; use `list_connector_info()` for the full
catalog, including known connectors that need an `extended-data[...]` extra.
Secret-like cache key fields such as `token`, `api_key`, `password`, and
`client_secret` are hashed before they are stored in the fabric cache.
`AWSConnector` and `GoogleConnector` are unified first-class classes: S3,
Organizations, SSO, Workspace, Cloud Resource Manager, Billing, and services
operations live on those connectors directly rather than on separate
`*Full` classes.
Google registry names are unified as well: use `google` for Workspace, Cloud,
Billing, and service discovery rather than split `google_*` connector aliases.
AWS Secrets Manager prefix loading is exposed as the generic
`load_secrets_by_prefix()` data method rather than as a vendor-specific helper.
AWS secret listing/deletion and Vault role filtering APIs use the canonical
`prefix` keyword; the old `name_prefix` convenience keyword is intentionally not
preserved.
Connector data payloads are promoted into Tier 2 containers at the boundary, so
decoded files, HTTP response data, GraphQL responses, and SDK-shaped maps can
use `ExtendedDict`, `ExtendedList`, and `ExtendedString` methods immediately.
Use `request_data_file()` when a connector workflow needs API response data and
non-secret provenance such as source URL, HTTP status, content type, method,
and endpoint in one `DataFile` artifact.
Data-returning AI tool wrappers expose the same `ExtendedDict`/`ExtendedList`
payload contract; framework factory functions still return framework tool
objects.
The generic CLI `call` command and MCP bridge expose only methods that
advertise Extended Data payload returns.
Serialized CLI/MCP boundaries and connector API error messages reuse the Tier 1
redaction primitives for common secret-bearing keys and token-shaped strings.
CLI and MCP connector calls pass method arguments through `values=[...]` as
context-sensitive diagnostic data, and connectors can add their own
operation-specific values for resource IDs, paths, URLs, emails, prompt text, or
vendor handles. Connector data methods can return structured vendor payloads
without making stdout, tool responses, logs, or raised transport errors a
secret leak by default. Raw SDK/client objects and raw transport responses
remain available from the methods that explicitly return them.

The `secrets` connector integrates with the standalone SecretSync project
(`jbcom/secrets-sync`) through the `secretsync` CLI. It expects
`secretsync pipeline --output json` to return the stable pipeline result
envelope used by this package.

```python
from extended_data import SecretsConnector, SyncOptions

result = SecretsConnector().run_pipeline(
    "pipeline.yaml",
    SyncOptions(dry_run=True),
)
```

The package is intentionally tiered:

- Tier 1 functions stay stateless and composable.
- Tier 2 containers inherit `UserString`, `UserDict`, `UserList`, immutable
  `tuple`, or `MutableSet`-compatible primitives and expose ergonomic methods
  over Tier 1 functions.
- Tier 3 processors use the first two tiers to handle files, inputs, API data,
  vendor integrations, and workflows.

Tier 3 decoders return Tier 2 containers by default, so
data files, Base64 payloads, and directed inputs can immediately use
`ExtendedDict`, `ExtendedList`, `ExtendedTuple`, `ExtendedSet`, and
`ExtendedString` methods.
`ExtendedList.filter_values()` exposes the Tier 1 allowlist/denylist list
filtering primitive as a chainable container operation.
`ExtendedList.split_by_type()`, `ExtendedTuple.split_by_type()`, and
`ExtendedDict.split_by_type()` expose the Tier 1 type-splitting primitives as
type-name keyed `ExtendedDict` results.
`ExtendedList.first_non_empty()` and `ExtendedTuple.first_non_empty()` expose
ordered non-empty selection while preserving promoted nested values.
`ExtendedList.zipmap()` and `ExtendedTuple.zipmap()` compose ordered key
containers with value iterables and return promoted `ExtendedDict` mappings.
`ExtendedDict.first_non_empty_value()` returns the first matching non-empty
value as promoted Tier 2 data, so selected nested maps and lists remain
chainable. Use `ExtendedDict.first_non_empty_entry()` and
`ExtendedDict.non_empty_entries()` when callers need selected key/value entries
instead of just the selected value.
Generic type routing can still ask for plain data roles with
`typeof(value, primitive_only=True)`, which treats Extended containers as their
underlying `str`, `list`, `dict`, and `set` roles.
String tokenization stays inside the same surface: `ExtendedString.split()`
returns an `ExtendedList` of `ExtendedString` values, and partition operations
return `ExtendedTuple` values. `ExtendedString.is_partial_match()` and
`ExtendedString.is_non_empty_match()` expose the Tier 1 matching primitives
without requiring callers to drop back to function-only utility code.
`ExtendedString.to_bool()`, `to_int()`, `to_float()`, `to_path()`,
`to_date()`, `to_datetime()`, and `to_time()` expose the Tier 1 scalar
conversion family as direct string-container methods.
`ExtendedString.decode_json()`, `decode_yaml()`, `decode_toml()`,
`decode_hcl2()`, and `decode_base64()` expose structured text decoding from
the string container and promote decoded maps/lists into Tier 2 data by
default.
`ExtendedString.reconstruct_special_type()` and the container
`reconstruct_special_types()` methods restore booleans, numbers, dates, times,
paths, and structured JSON/YAML values while staying in promoted Tier 2 data.
Container `to_export_safe()` and `wrap_for_export()` methods expose the Tier 3
export boundary directly from promoted values for JSON, YAML, TOML, HCL, and
raw string output.
Format encoders lower extended containers, including extended mapping keys, at
the serialization boundary.
`read_data_file()` is the direct file boundary for one-step read plus decode
workflows; it raises for missing files and promotes structured data into Tier 2
containers by default. `DataFile` makes one decoded file or URL artifact
first-class with promoted data, promoted source metadata, detached
`as_extended()` views, direct write/export helpers, and a `workflow()` bridge
for artifact-first processing. DataFile source labels and metadata use the
shared Tier 1 redaction policy before they enter workflow steps or result
metadata. `DataWorkflow` makes multi-step compositions first-class: read,
decode, or accept a `DataFile` artifact, apply named
transformations, write an output artifact, and keep the step trail in a
`WorkflowResult`. Workflow metadata is promoted and preserved across
transformations, lowering/promoting, and writes, so file and API provenance can
stay with the result. Completed workflow results expose detached promoted views
with `as_extended()` plus direct `to_export_safe()` and `wrap_for_export()`
helpers. Missing file inputs and empty writes fail loudly.
`InputProvider` stores its active, frozen, and merged input snapshots as
`ExtendedDict` values, so direct input-data access can use Tier 2 container
methods. `snapshot_inputs()` returns detached active or frozen snapshots, and
`replace_inputs()` installs a new active snapshot while clearing stale frozen
state by default. `get_input()` remains the scalar coercion boundary for
booleans, numbers, paths, datetimes, and credential strings; pass
`as_extended=True` when an injected raw or fallback input value should stay in
Tier 2 form and keep using container methods such as `reconstruct_special_types()`
and `to_export_safe()`.
`Logging` stores marked log message collections as `ExtendedDict` and
`ExtendedSet` values while keeping Python logger and handler objects plain.
Use `get_stored_messages()` or `snapshot_stored_messages()` when downstream
data workflows need detached promoted copies of collected messages. Runtime log
messages and attached JSON payloads use the same Tier 1 redaction policy as
connector diagnostics, and `exit_run()` formatting failures report redacted
result snapshots instead of raw payload data.

More detail lives in [`docs/package-surface.md`](docs/package-surface.md).

## Development

```bash
uv sync --extra tests --extra typing
uv run --with pip-audit==2.10.0 pip-audit --skip-editable
uv run pytest
uv run ruff check src tests
uv run mypy src/extended_data
uv build
```

## License

MIT.
