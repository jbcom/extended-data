# Ownership Map

`extended-data` owns the base data layer. Surfaces outside that boundary were
moved into repositories where their dependencies, docs, tests, and release
cadence are first-class.

## In This Package

| Surface | Current owner |
| --- | --- |
| Pure data functions | `extended_data.primitives` |
| Generic and shape-specific extended containers | `extended_data.containers` |
| File import/export and codecs | `extended_data.io` |
| Workflow composition and local file sync primitives | `extended_data.workflows` |
| Input loading and decorators | `extended_data.inputs` |
| Structured lifecycle logging | `extended_data.logging` |

## Moved Out

| Prior surface | Current repository | Install target |
| --- | --- | --- |
| External vendor API clients | `jbcom/vendor-fabric` | `vendor-fabric` |
| Vendor fabric MCP and tool adapters | `jbcom/vendor-fabric` | `vendor-fabric[...]` |
| Meshy, Slack, Google, GitHub, AWS, Vault, Zoom, Anthropic, Cursor integrations | `jbcom/vendor-fabric` | `vendor-fabric[...]` |
| Vendor-backed Python sync capabilities | `jbcom/vendor-fabric` | `vendor-fabric[secrets-sync]` |
| SecretSync agent tool wrappers | `jbcom/vendor-fabric` | `vendor-fabric[ai,secrets-sync]` |
| Agent framework integrations | `jbcom/vendor-fabric` | `vendor-fabric[ai]` |

The old in-package connector and secrets namespaces are intentionally absent.
That is a clean major-version boundary: code should depend on the package that
owns the capability it uses.

## Dependency Direction

The intended layering is dependency-inward:

```text
extended-data
  <- vendor-fabric
```

`extended-data` has no dependency on the higher layers. Higher layers may use
`extended-data` primitives, containers, input handling, workflows, and logging
without reimplementing those base concerns.
