# Extended Data Workspace

![Extended Data — structured values crossing clear data boundaries](https://raw.githubusercontent.com/jbcom/extended-data/main/docs/assets/extended-data-hero.png)

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

The Sourcey documentation site lives in `docs/` and deploys to
<https://extended-data.dev>. It is separate from the Python `uv` workspace.
