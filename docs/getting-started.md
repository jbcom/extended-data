# Getting Started

Install the base package:

```bash
pip install extended-data
```

Use extras when a workflow needs vendor SDKs or framework adapters:

```bash
pip install "extended-data[aws,google,github,slack,vault]"
pip install "extended-data[meshy,mcp,webhooks]"
pip install "extended-data[ai]"
```

## First Workflow

```python
from extended_data import DataWorkflow, ExtendedDict, Logging
from extended_data.primitives import decode_json, encode_yaml, number_to_words

logger = Logging(logger_name="docs")
payload = ExtendedDict(decode_json('{"service": {"name": "api"}}'))

result = (
    DataWorkflow.from_value(payload, metadata={"source": "inline"})
    .merge({"replicas": 3}, name="merge-runtime")
    .transform("unhump")
    .result()
)

logger.info("prepared config", data=result.as_builtin())
print(payload["service"]["name"].upper_first())
print(number_to_words(42))
print(encode_yaml(result.as_builtin()))
```

## Connector Catalog

```python
from extended_data import ConnectorFabric, InputProvider

inputs = InputProvider(inputs={"GITHUB_OWNER": "jbcom"}, from_environment=False)
fabric = ConnectorFabric(inputs=inputs.inputs)

print(fabric.list_connectors())
print(fabric.list_available_connectors())
print(fabric.list_connectors_by_category("development"))
```

`list_connectors()` returns the known catalog, including integrations whose
optional SDK extras are not installed. Use `list_available_connectors()` when a
runtime needs only integrations that can actually be constructed in the current
environment.

## Local Development

```bash
git clone https://github.com/jbcom/extended-data.git
cd extended-data
uv sync --all-extras --dev
tox -e lint,typecheck,audit,py311,py312,py313,py314,examples,docs,build
```
