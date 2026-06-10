# Publishing Checklist

`extended-data` releases are automated from `main` with release-please and
PyPI trusted publishing. Do not hand-edit versions, changelog entries, release
tags, or GitHub releases during the normal release path.

## Release Model

- `release-please` owns version detection, changelog updates, release PRs, and
  Git tags.
- The package name is `extended-data`; PyPI publication uses the tighter
  `extended-data` distribution name.
- The release workflow publishes only after release-please reports that a
  release was created.
- The PyPI job uses OIDC trusted publishing through `uv publish`; no PyPI token
  should be stored in repository secrets for the normal path.

## Maintainer Preflight

Run these before merging a release PR or manually dispatching release workflow
diagnostics:

```bash
uv sync --extra tests --extra typing
uv run --with pip-audit==2.10.0 pip-audit --skip-editable
uv run ruff check .
uv run mypy src/extended_data
uv run pytest
uv build
```

## Workflow Hygiene

- Keep `.github/workflows/*.yml` actions pinned to exact commit SHAs.
- Update adjacent version comments when refreshing action SHAs.
- Use `gh` to verify latest stable action releases before changing pins.
- Keep top-level `permissions: {}` and grant only job-scoped permissions.

Current workflow action pins:

| Action | Stable version | Commit SHA |
| --- | --- | --- |
| `actions/checkout` | `v6.0.3` | `df4cb1c069e1874edd31b4311f1884172cec0e10` |
| `actions/setup-python` | `v6.2.0` | `a309ff8b426b58ec0e2a45f0f869d46889d02405` |
| `astral-sh/setup-uv` | `v8.2.0` | `fac544c07dec837d0ccb6301d7b5580bf5edae39` |
| `googleapis/release-please-action` | `v5.0.0` | `45996ed1f6d02564a971a2fa1b5860e934307cf7` |

## Publishing Flow

1. Land normal feature, fix, docs, and maintenance commits using Conventional
   Commit prefixes.
2. Let the release workflow open or update the release-please PR.
3. Review the release PR for the expected changelog and manifest updates.
4. Merge the release PR.
5. Confirm the release workflow created the GitHub release and published to
   PyPI through trusted publishing.
6. Verify the package can be installed from PyPI:

```bash
python -m pip install extended-data
python -c "import extended_data; print(extended_data.__version__)"
```

## Manual Repairs

Manual tags or PyPI uploads are repair paths, not the release process. If a
release workflow fails after release-please creates a tag:

1. Keep the failed tag intact while diagnosing unless the release is proven
   unrecoverable.
2. Prefer rerunning the failed workflow job.
3. If a bad GitHub release was published, delete only the bad artifacts needed
   for repair.
4. Document the repair in the PR or release notes.
