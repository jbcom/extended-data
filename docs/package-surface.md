# Package Surface

`extended-data` is one Python distribution with a single `extended_data`
namespace. The root package exposes the primitives users need most often:

```python
from extended_data import (
    ConnectorFabric,
    InputProvider,
    Logging,
    decode_json,
    encode_yaml,
    flatten_map,
)
```

## Layers

- Core data primitives handle serialization, file decoding, type coercion,
  string transforms, map/list transforms, and export-safe values.
- `InputProvider` loads input data from explicit mappings, environment
  variables, and stdin, then decodes or coerces values through the same core
  primitives.
- `Logging` provides structured lifecycle logging for applications and
  connector workflows.
- `ConnectorFabric` caches and coordinates vendor connectors while sharing
  input loading, logging, data normalization, retry behavior, and serialization.

## Optional Integrations

Install only the vendor or AI layers you need:

```bash
pip install "extended-data[aws,github,vault]"
pip install "extended-data[google,slack,zoom]"
pip install "extended-data[ai]"
pip install "extended-data[meshy,mcp]"
```

Optional dependency checks live in `extended_data.connectors._optional`; there
are no old package compatibility shims in the public API.
