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
