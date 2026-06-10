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
pip install "extended-data[ai]"
pip install "extended-data[meshy,mcp]"
pip install "extended-data[secrets]"
```

## Usage

```python
from extended_data import decode_json, encode_yaml
from extended_data.inputs import directed_inputs
from extended_data.logging import Logging
from extended_data.connectors.github import GitHubConnector

logger = Logging(logger_name="example")
data = decode_json('{"status": "ok"}')
print(encode_yaml(data))
```

## Package Shape

```text
extended_data/
  core serialization, files, types, transforms
  inputs/
  logging/
  connectors/
  secrets/
  workflows/
```

Vendor connectors are first-class adapters in the data fabric. They share the
same primitives for input loading, structured logging, data normalization,
retry behavior, and serialization.

## Development

```bash
uv sync --extra tests --extra typing
uv run pytest
uv run ruff check src tests
uv build
```

## License

MIT.
