# Getting Started

Install the base package:

```bash
pip install extended-data
```

## First Workflow

```python
from extended_data import DataWorkflow, ExtendedDict, Logging
from extended_data.primitives import decode_json, encode_yaml, number_to_words

logger = Logging(logger_name="docs", enable_console=False, enable_file=False)
payload = ExtendedDict(decode_json('{"service": {"name": "api"}}'))

result = (
    DataWorkflow.from_value(payload, metadata={"source": "inline"})
    .merge({"replicas": 3}, name="merge-runtime")
    .transform("unhump")
    .result()
)

logger.logged_statement("prepared config", json_data=result.as_builtin(), log_level="info")

assert payload["service"]["name"].upper_first() == "Api"
assert number_to_words(42) == "forty-two"
assert "replicas: 3" in encode_yaml(result.as_builtin())
```

## Inputs And Logging

```python
from extended_data import InputProvider, Logging

inputs = InputProvider(inputs={"SERVICE_NAME": "api"}, from_environment=False)
logger = Logging(logger_name="example", enable_console=False, enable_file=False)

logger.logged_statement("loaded inputs", json_data={"service": inputs.inputs["SERVICE_NAME"]}, log_level="info")

assert inputs.inputs["SERVICE_NAME"] == "api"
```

## Local Development

```bash
git clone https://github.com/jbcom/extended-data.git
cd extended-data
uv sync --all-extras --dev
tox -e lint,typecheck,audit,py311,py312,py313,py314,examples,docs,build
```
