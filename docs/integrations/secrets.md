# SecretSync Bridge

SecretSync is intentionally its own Go product repository:

- GitHub: [jbcom/secrets-sync](https://github.com/jbcom/secrets-sync)
- CLI install path: `go install github.com/jbcom/secrets-sync/cmd/secrets-sync@latest`

`extended-data` provides the Python data bridge for inspecting pipeline
configuration, validating options, and preparing dry-run sync workflows.

```python
from extended_data import SecretsConnector, SyncOptions

connector = SecretsConnector()
options = SyncOptions(source="vault", target="aws", dry_run=True)
result = connector.sync(options)

print(result.status)
print(result.to_export_safe("json"))
```

Use the Go repository for production CLI releases, GitHub release assets, and
operational runbooks. Use `extended-data[secrets]` when Python workflows need to
compose SecretSync-shaped data with the rest of the Extended Data primitives and
workflows.
