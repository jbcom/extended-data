# Extended Data

Comprehensive Python data utilities for serialization, configuration inputs,
structured logging, file processing, and workflow composition.

The public API lives under one `extended_data` namespace with three deliberate
tiers:

- Tier 1: pure functions for codecs, string transforms, redaction, matching,
  type coercion, mapping, sequence, and state utilities.
- Tier 2: `ExtendedString`, `ExtendedDict`, `ExtendedList`, `ExtendedTuple`,
  and `ExtendedSet` containers that expose Tier 1 operations as methods.
- Tier 3: data processors that compose the first two tiers for files, inputs,
  logging, export/import boundaries, and workflows.

External API clients live in the separate `vendor-connectors` distribution.
SecretSync's Python bridge lives in `secrets-sync-bridge`.

## Install

```bash
pip install extended-data
```

Development and documentation extras are available for contributors:

```bash
pip install "extended-data[dev]"
pip install "extended-data[docs]"
```

## Usage

```python
from extended_data import DataFile, DataWorkflow, ExtendedDict, InputProvider, Logging, decode_file
from extended_data.primitives import decode_json, encode_yaml, number_to_words, redact_sensitive_text

logger = Logging(logger_name="example", enable_console=False, enable_file=False)
inputs = InputProvider(inputs={"SERVICE_NAME": "api"}, from_environment=False)
data = decode_json('{"service": {"name": "api"}}')
payload = ExtendedDict(data).deep_merge({"replicas": 3})
decoded_file = decode_file('{"service": {"name": "worker"}}', suffix="json")
artifact = DataFile.decode("service:\n  name: api\n", suffix="yaml")
workflow = DataWorkflow.from_value(payload).transform("unhump").result()

logger.logged_statement("prepared workflow", json_data=workflow.as_builtin(), log_level="info")

assert inputs.inputs["SERVICE_NAME"] == "api"
assert decoded_file["service"]["name"].upper_first() == "Worker"
assert artifact.metadata["encoding"] == "yaml"
assert number_to_words(42) == "forty-two"
assert redact_sensitive_text("Authorization: Bearer raw_token") == "Authorization: [REDACTED]"
assert "replicas: 3" in encode_yaml(workflow.as_builtin())
```

The installed CLI exposes the Tier 3 data boundary:

```bash
extended-data decode '{"service": {"name": "api"}}' --suffix json
extended-data decode --file config.yaml --output json
extended-data inspect --file config.yaml
extended-data merge config/base.yaml config/dev.yaml --output yaml
extended-data transform --file payload.json --step reconstruct --step unhump
```

## Package Shape

```text
extended_data/
  containers/   Tier 2 ExtendedString/Dict/List/Tuple/Set wrappers
  inputs/       InputProvider and decorator-based input injection
  io/           Tier 3 file, import, export, and base64 processors
  logging/      structured lifecycle logging
  primitives/   Tier 1 pure functions and codecs
  workflows/    Tier 3 higher-order workflow composition
```

Tier 1 primitive names are explicit in this major version and live under
`extended_data.primitives`, not the package root. Use `bytes_to_string()` for
bytes-like coercion and `string_to_bool()`, `string_to_int()`,
`string_to_float()`, `string_to_path()`, `string_to_date()`,
`string_to_datetime()`, and `string_to_time()` for scalar string conversion.
Use `redact_sensitive_text()` and `redact_sensitive_data()` for diagnostic and
JSON-like payload redaction. Pass `values=[...]` when a caller knows specific
context values, such as resource IDs, emails, paths, or URLs, must be withheld
in addition to common secret fields.

Tier 2 containers inherit from standard Python collection primitives and expose
chainable data operations. For example, `ExtendedString.decode_json()` promotes
JSON into extended containers, `ExtendedDict.reconstruct_special_types()` turns
string scalars into booleans/numbers/dates where safe, and
`ExtendedList.first_non_empty()` returns the first meaningful value without
lowering the surrounding data boundary.

Tier 3 processors keep structured data moving through explicit boundaries.
`DataFile` reads, decodes, tracks metadata, and exports structured files.
`DataWorkflow` layers reads, merges, transforms, writes, and provenance into a
single result object. `InputProvider` loads direct inputs and environment data,
and `Logging` provides structured lifecycle logging with stored-message
snapshots returned as extended containers.

The old `extended_data_types`, `directed_inputs_class`, and `lifecyclelogging`
package names are not shimmed. The removed `extended_data.connectors` and
`extended_data.secrets` namespaces are also not preserved. Clean-break import
failures are intentional so stale migrations are visible.

## Local Development

```bash
uv sync --all-extras --dev
tox -e lint
tox -e typecheck
tox -e py311,py312,py313,py314
tox -e examples
tox -e docs
tox -e build
```
