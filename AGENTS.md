# Repository Instructions

This repository contains the `extended-data` Python package family as a `uv`
workspace.

Use the canonical checkout only:

```bash
~/src/jbcom/extended-data
```

Do not create side worktrees for this repository. If useful work exists in
another checkout, move it into this checkout before continuing.

## Workspace Packages

| Distribution | Package path | Purpose |
| --- | --- | --- |
| `extended-data` | `packages/extended-data` | Runtime data primitives, containers, IO, workflows, inputs, logging, docs, and CLI |
| `pytest-extended-data` | `packages/pytest-extended-data` | Reusable pytest fixtures and assertions for Extended Data consumers |

The workspace root is not a published Python distribution.

## Package Scope

`extended-data` owns:

- Tier 1 pure data primitives under `extended_data.primitives`
- Tier 2 extended containers under `extended_data.containers`
- Tier 3 file, import, export, workflow, input, and logging processors
- Sphinx/Furo/autodoc2 documentation for this package
- release-please, CD, PyPI publishing, and GitHub Pages for this package

`pytest-extended-data` owns:

- reusable pytest fixtures for consumers that need representative Extended Data
  values
- assertion helpers for shape and built-in round-trip checks
- the `pytest11` entry point for automatic plugin loading

`extended-data` does not own vendor SDKs, provider connectors, SecretSync vendor
behavior, agent runtimes, or agent framework adapters. Those belong to
`vendor-fabric` and `agentic-fabric`.

## Related Repositories

`extended-data` is the base layer. It does not wait on downstream repositories.

| Layer | Local checkout | Remote |
| --- | --- | --- |
| Base data | `~/src/jbcom/extended-data` | `https://github.com/jbcom/extended-data` |
| Vendor layer | `~/src/jbcom/vendor-fabric` | `https://github.com/jbcom/vendor-fabric` |
| Agent layer | `~/src/jbcom/agentic-fabric` | `https://github.com/jbcom/agentic-fabric` |
| Legacy monorepo | `~/src/jbcom/extended-data-library` | `https://github.com/jbcom/extended-data-library` |

## Architecture Docs

Read these before changing code:

- `packages/extended-data/docs/architecture.rst`: `ExtendedData` superclass
  and tier design
- `packages/extended-data/docs/pillars.rst`: package ownership principles
- `packages/extended-data/docs/ownership-map.rst`: moved surfaces and
  destination repositories

Do not migrate vendor connector or SecretSync provider code into this
repository.

## Development Rules

- Keep `ExtendedData` as the common superclass and polymorphic constructor.
- Ensure extended containers preserve native Python behavior.
- Ensure nested mutations promote built-in values into extended containers.
- Keep old namespace shims removed.
- Use Python warnings, exceptions, and logging primitives in library code; keep
  runtime `print()` paths limited to CLI and examples.
- Keep README, Sphinx guides, examples, and tests aligned with the public API.
- Keep public docs in reStructuredText under `packages/extended-data/docs/`; do
  not add authored Markdown pages there.
- Build docs with Sphinx/Furo/autodoc2 and warnings as errors.
- Keep examples under test through `packages/extended-data/tests/examples`.
- Keep pytest-specific developer hooks in `pytest-extended-data`; do not hide
  pytest plugin behavior in the runtime package.

## Preferred Commands

```bash
uv sync --all-packages --all-extras --dev
tox -e lint
tox -e typecheck
tox -e py311,py312,py313,py314
tox -e examples
tox -e docs
tox -e build
```

Use `uvx --with tox-uv --with tox-gh tox -e <env>` when tox is not installed
locally.

Do not set `skip_missing_interpreters = true`. Python 3.11, 3.12, 3.13, and
3.14 are all part of the supported release contract.

## Release Flow

- Open ready pull requests by default, not draft pull requests.
- Resolve CI failures and actionable review feedback before merge.
- Squash merge only when the pull request is green and review feedback is
  addressed.
- Keep release-please configured for conventional commits so it can open release
  pull requests.
- CD must build and publish packages to PyPI through trusted publishing.
  `extended-data` uses `.github/workflows/cd.yml`; `pytest-extended-data` uses
  `.github/workflows/cd-pytest-extended-data.yml` so PyPI can register a
  distinct trusted publisher for the plugin package.
- Tagged `extended-data` releases must also deploy GitHub Pages docs.
