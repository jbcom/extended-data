# Ownership Map

`extended-data` owns the base data layer. Surfaces outside that boundary were
moved into repositories where their dependencies, docs, tests, and release
cadence are first-class.

## In This Package

| Surface | Current owner |
| --- | --- |
| Pure data functions | `extended_data.primitives` |
| Extended containers | `extended_data.containers` |
| File import/export and codecs | `extended_data.io` |
| Workflow composition | `extended_data.workflows` |
| Input loading and decorators | `extended_data.inputs` |
| Structured lifecycle logging | `extended_data.logging` |

## Moved Out

| Prior surface | Current repository | Install target |
| --- | --- | --- |
| External cloud and vendor API clients | `jbcom/cloud-connectors-python` | `cloud-connectors` |
| Cloud connector MCP and tool adapters | `jbcom/cloud-connectors-python` | `cloud-connectors[...]` |
| Meshy, Slack, Google, GitHub, AWS, Vault, Zoom, Anthropic, Cursor integrations | `jbcom/cloud-connectors-python` | `cloud-connectors[...]` |
| SecretSync Python bridge | `jbcom/secrets-sync` | `secrets-sync-bridge` |
| SecretSync agent tool wrappers | `jbcom/agent-orchestration` | `agentic-crew[secrets-sync]` |
| Agent framework integrations | `jbcom/agent-orchestration` | `agentic-crew[...]` |

The old in-package connector and secrets namespaces are intentionally absent.
That is a clean major-version boundary: code should depend on the package that
owns the capability it uses.

## Dependency Direction

The intended layering is dependency-inward:

```text
extended-data
  <- cloud-connectors
  <- secrets-sync-bridge

cloud-connectors + secrets-sync-bridge
  <- agentic-crew
```

`extended-data` has no dependency on the higher layers. Higher layers may use
`extended-data` primitives, containers, input handling, workflows, and logging
without reimplementing those base concerns.
