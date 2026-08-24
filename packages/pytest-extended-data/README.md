# pytest-extended-data

`pytest-extended-data` publishes reusable pytest fixtures and assertions for
projects built on `extended-data`.

Install it in test environments:

```bash
uv add --dev pytest-extended-data
```

The plugin is exposed through the standard `pytest11` entry point. It provides:

- `extended_data_factory`: the `ExtendedData` polymorphic constructor.
- `extended_data_payload`: a small nested mapping payload for examples and smoke tests.
- `extended_data_value`: the payload wrapped as an `ExtendedData` value.
- `assert_extended_shape(value, shape)`: assertion helper for shape checks.
- `assert_builtin_round_trip(value, expected)`: assertion helper for export-boundary checks.

Use the fixtures as consumer-facing contract checks, rather than duplicating
private container implementation details in every downstream package:

```python
def test_configuration_boundary(extended_data_value):
    assert extended_data_value["service"]["name"] == "api"
    assert extended_data_value.as_builtin() == {
        "service": {"name": "api", "ports": [8080, 8443]},
        "enabled": True,
    }
```

The runtime package deliberately has no pytest plugin. Install this package
only in test environments so production dependencies remain focused on data
handling.

See the [Package Surface guide](https://extended-data.dev/guides/package-surface.html)
for the runtime and plugin split.
