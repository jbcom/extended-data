# Inputs

The old directed inputs package is now first-class under `extended_data.inputs`
and the package root.

```python
from extended_data import InputProvider

provider = InputProvider(
    inputs={"APP_DEBUG": "true", "APP_REPLICAS": "3"},
    from_environment=False,
)

print(provider.get_input("APP_DEBUG", as_type=bool))
print(provider.snapshot_inputs())
```

## Decorators

```python
from extended_data import directed_inputs, input_config

@directed_inputs(inputs={"SERVICE_NAME": "api"}, from_environment=False)
class ServiceConfig:
    @input_config(service="SERVICE_NAME")
    def build(self, service: str) -> dict[str, str]:
        return {"service": service}

print(ServiceConfig().build())
```

Inputs are promoted into Extended Data containers at the boundary, so decoded
JSON/YAML/Base64 payloads can continue into Tier 2 and Tier 3 workflows without a
separate adapter layer.
