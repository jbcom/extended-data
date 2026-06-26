# Publishing

`extended-data` uses release-please, GitHub Releases, and PyPI trusted
publishing.

## Local Gates

```bash
tox -e lint,typecheck,audit,py311,py312,py313,py314,examples,docs,build
```

## Release Flow

1. Merge feature, fix, docs, and maintenance commits to `main`.
2. `cd.yml` runs release-please and opens or updates the release PR.
3. Merge the release PR.
4. release-please creates the GitHub release and version tag.
5. `release.yml` runs from the tag and publishes to PyPI with OIDC trusted
   publishing.

Manual tags and manual PyPI uploads are repair paths, not the normal release
process.
