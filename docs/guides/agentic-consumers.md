# Agentic Consumers

`extended-data` is useful to code-generating tools and agent runtimes for the
same reason it is useful to application code: it makes a data boundary
explicit. It is not an agent framework, a vendor SDK, a credential manager, or
a place to put provider-specific control flow.

## Use the public data contract

Use the smallest layer that completes the task:

1. Import one pure operation from `extended_data.primitives` for parsing,
   coercion, normalization, encoding, matching, or redaction.
2. Promote uncertain structured input with `ExtendedData(value)` when the
   shape can be a mapping, sequence, or scalar.
3. Use `DataFile` or `DataWorkflow` for a named file or transformation
   boundary. Keep the result as extended data until the caller explicitly
   needs built-ins.

```python
from extended_data import ExtendedData
from extended_data.primitives import decode_json, redact_sensitive_data

raw = decode_json('{"service": {"name": "api"}, "token": "do-not-log"}')
payload = ExtendedData(raw).merge({"replicas": 2})
safe_for_diagnostics = redact_sensitive_data(payload.as_builtin())

assert payload["service"]["name"].upper_first() == "Api"
assert safe_for_diagnostics["token"] == "[REDACTED]"
```

## Preserve the boundary

Do not flatten a value merely to call a method. Nested literals are promoted
when they enter Extended Data containers, so normal indexing and mutation keep
the Tier 2 methods available. Conversely, call `as_builtin()` or `to_builtin()`
only when crossing into a serializer, an external API client, or a library
whose contract specifically requires built-in Python values.

Treat redaction as a diagnostic boundary, not as a substitute for access
control. Redact before a value is logged, displayed, or attached to an error;
do not place credentials in prompts, source files, fixtures, or workflow
metadata.

## Keep ownership clear

This package owns data mechanics only. It must not acquire provider SDKs,
vendor API clients, secret-sync behavior, MCP adapters, agent runtime state, or
framework-specific tools. Those integrations belong to `vendor-fabric` and
`agentic-fabric`; they should consume this package's public data contract
instead of extending its internals.

Do not restore removed compatibility imports such as `extended_data.connectors`
or `extended_data.secrets`. A failed import is an intentional migration signal.

## Test downstream integrations

Install `pytest-extended-data` in a consumer's test environment to get a small
representative payload, the polymorphic factory, and assertions for the plain
export boundary:

```bash
uv add --dev pytest-extended-data
```

```python
from pytest_extended_data import assert_builtin_round_trip


def test_export_contract(extended_data_value):
    assert_builtin_round_trip(
        extended_data_value,
        {"service": {"name": "api", "ports": [8080, 8443]}, "enabled": True},
    )
```

Before generating a broad integration, consult the [Package Surface](package-surface.md),
[containers guide](../core/containers.md), and generated [API reference](../reference/index.md).
They are the source of truth for stable imports and behavior.
