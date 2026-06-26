# Package Surface

`extended-data` is a base Python data package. Its public contract is the
`extended_data` namespace plus the console command `extended-data`.

## Tier 1 Primitives

Pure functions live under `extended_data.primitives`. These functions cover
structured serialization, scalar coercion, matching, key normalization,
sequence/mapping utilities, state predicates, stack inspection, and redaction.

```python
from extended_data.primitives import decode_json, encode_yaml, redact_sensitive_text

payload = decode_json('{"service": "api"}')

assert payload == {"service": "api"}
assert "service: api" in encode_yaml(payload)
assert redact_sensitive_text("token=abc") == "token=[REDACTED]"
```

Tier 1 names are intentionally not exported from the package root. Import them
from `extended_data.primitives` so the root remains reserved for cohesive data
surfaces.

## Tier 2 Containers

Extended containers promote decoded data into ergonomic objects:

- `ExtendedString`
- `ExtendedDict`
- `ExtendedList`
- `ExtendedTuple`
- `ExtendedSet`

```python
from extended_data import ExtendedDict, ExtendedList, ExtendedString

assert ExtendedString("api-gateway").to_snake_case() == "api_gateway"
assert ExtendedList([None, "", {"service": "api"}]).first_non_empty()["service"] == "api"
assert ExtendedDict({"enabled": "true"}).reconstruct_special_types()["enabled"] is True
```

The containers keep Python collection behavior while adding methods that route
through Tier 1 primitives.

## Tier 3 Processors

Tier 3 surfaces compose primitives and containers for real data movement:

- `DataFile` reads, decodes, tracks metadata, and exports structured files.
- `DataWorkflow` layers file reads, merges, transforms, writes, and provenance.
- `InputProvider` loads direct inputs and environment data.
- `Logging` handles structured lifecycle logging and returns stored snapshots
  as extended containers.

```python
from extended_data import DataFile, DataWorkflow, InputProvider, Logging

artifact = DataFile.decode("service:\n  name: api\n", suffix="yaml")
workflow = DataWorkflow.from_value(artifact.data).merge({"replicas": 2}).result()
inputs = InputProvider(inputs={"ENV": "dev"}, from_environment=False)
logger = Logging(logger_name="docs", enable_console=False, enable_file=False)

logger.logged_statement("workflow ready", json_data=workflow.as_builtin(), log_level="info")

assert artifact.metadata["encoding"] == "yaml"
assert workflow.as_builtin()["replicas"] == 2
assert inputs.inputs["ENV"] == "dev"
```

## CLI

The `extended-data` command exposes the same file and workflow boundary:

```bash
extended-data decode '{"service": {"name": "api"}}' --suffix json
extended-data decode --file config.yaml --output json
extended-data inspect --file config.yaml
extended-data merge config/base.yaml config/dev.yaml --output yaml
extended-data transform --file payload.json --step reconstruct --step unhump
```

## Split Packages

`vendor-connectors` owns external API clients, optional vendor SDK dependencies,
MCP/tool adapters, and vendor-specific examples. `secrets-sync-bridge` owns the
Python bridge to the `secrets-sync` Go CLI.

`extended-data` does not preserve `extended_data.connectors`,
`extended_data.secrets`, `extended_data_types`, `directed_inputs_class`, or
`lifecyclelogging` compatibility shims. Those import failures are intentional in
this major version.
