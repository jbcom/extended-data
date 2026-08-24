# Extended Data

![Extended Data — structured values crossing clear data boundaries](https://raw.githubusercontent.com/jbcom/extended-data/main/docs/assets/extended-data-hero.png)

Extended Data is a Python package family for moving structured values across
clear boundaries: parsing input, normalizing and transforming it, preserving
ergonomic container behavior, and exporting a plain built-in value when it is
time to write or hand data to another library.

Start with the [documentation site](https://extended-data.dev), especially the
[Getting Started](https://extended-data.dev/guides/getting-started.html) and
[Package Surface](https://extended-data.dev/guides/package-surface.html) guides.

## Install and choose a layer

```bash
pip install extended-data
```

Most application code needs only these three choices:

1. Use `extended_data.primitives` for a single deterministic conversion,
   serialization operation, transform, or redaction step.
2. Use `ExtendedData(value)` at an uncertain data boundary. It returns the
   right extended shape (`ExtendedDict`, `ExtendedList`, `ExtendedString`, and
   so on) while retaining normal Python collection behavior.
3. Use `DataFile` or `DataWorkflow` when reading, merging, transforming, or
   writing a structured artifact is the actual unit of work.

```python
from extended_data import DataWorkflow, ExtendedData
from extended_data.primitives import decode_json, encode_yaml

incoming = decode_json('{"service": {"name": "api"}}')
config = ExtendedData(incoming).merge({"replicas": 2})

result = (
    DataWorkflow.from_value(config)
    .transform("unhump")
    .result()
)

assert result.as_extended()["service"]["name"] == "api"
assert "replicas: 2" in encode_yaml(result.as_builtin())
```

`ExtendedData` promotes nested values as they enter or mutate containers. Use
`as_builtin()` (or `to_builtin()`) at an explicit export boundary when an API,
serializer, or third-party library needs ordinary Python `dict`, `list`,
`str`, and scalar values.

## Consumers that generate or operate code

Automated and agentic consumers should use the same public contract as human
callers: import pure functions from `extended_data.primitives`, promote unknown
payloads with `ExtendedData`, and lower values only at explicit boundaries.
The [agentic consumer guide](https://extended-data.dev/guides/agentic-consumers.html)
sets out the safe integration rules, test plugin, and package ownership limits.

## Packages

| Distribution | Package path | Purpose |
| --- | --- | --- |
| `extended-data` | `packages/extended-data` | Runtime data primitives, containers, IO, workflows, inputs, logging, docs, and CLI |
| `pytest-extended-data` | `packages/pytest-extended-data` | Reusable pytest fixtures and assertion helpers for Extended Data consumers |

The workspace root is not a published Python distribution. Install a package,
not the repository root, in downstream applications.

## Common Commands

```bash
uv sync --all-packages --all-extras --dev
tox -e lint,typecheck,audit,py311,py312,py313,py314,examples,docs,build
pnpm docs:validate
```

The Sourcey documentation source lives in `docs/` and deploys to
<https://extended-data.dev>. It is independently locked from the Python `uv`
workspace so documentation builds remain deterministic.
