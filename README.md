# Extended Data Workspace

This repository is a `uv` workspace for the Extended Data package family.

## Packages

| Distribution | Package path | Purpose |
| --- | --- | --- |
| `extended-data` | `packages/extended-data` | Runtime data primitives, containers, IO, workflows, inputs, logging, docs, and CLI |
| `pytest-extended-data` | `packages/pytest-extended-data` | Reusable pytest fixtures and assertion helpers for Extended Data consumers |

The workspace root is not a published Python distribution.

## Common Commands

```bash
uv sync --all-packages --all-extras --dev
tox -e lint,typecheck,audit,py311,py312,py313,py314,examples,docs,build
```

Runtime package docs live in `packages/extended-data/docs` and deploy to
<https://extended-data.dev>.
