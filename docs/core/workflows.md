# Workflows

Tier 3 processors use primitives and containers to handle file, API, and
workflow boundaries.

## DataFile

```python
from extended_data import DataFile, read_data_file

artifact = DataFile.decode('{"service": {"name": "api"}}', suffix="json")
print(artifact.data["service"]["name"].upper_first())
print(artifact.metadata["encoding"])

loaded = read_data_file("config/service.yaml")
print(loaded["service"]["name"].upper_first())
```

`DataFile` keeps source labels and metadata promoted and redacted before they
enter workflow step names or result metadata.

## DataWorkflow

```python
from extended_data import DataWorkflow

result = (
    DataWorkflow.from_file("config/base.yaml")
    .merge_file("config/dev.yaml", name="merge-dev")
    .transform("reconstruct", "unhump")
    .write("build/config.yaml")
)

print(result.steps)
print(result.as_extended())
print(result.as_builtin())
```

The CLI exposes the same data boundary:

```bash
extended-data decode '{"service": {"name": "api"}}' --suffix json
extended-data inspect --file config.yaml
extended-data merge config/base.yaml config/dev.yaml --output yaml
extended-data transform --file payload.json --step reconstruct --step unhump
```
