Publishing Checklist
====================

``extended-data`` uses the standard ``ci.yml`` > ``release.yml`` >
``cd.yml`` workflow shape. ``release.yml`` owns release-please. When a
release-please PR merge creates a release tag, it dispatches ``cd.yml``
for package publication and the Sphinx/Furo documentation deploy. Do not
hand-edit versions, changelog entries, release tags, or GitHub releases
during the normal release path.

Release Model
-------------

- ``release.yml`` owns release-please version detection, changelog
  updates, release PRs, Git tags, and dispatching ``cd.yml`` after a
  release is created.
- ``cd.yml`` owns tag-gated package verification, PyPI publication, and
  GitHub Pages publication for ``extended-data.dev``.
- The package name is ``extended-data``; PyPI publication uses the
  tighter ``extended-data`` distribution name.
- The CD workflow publishes only for the release tag passed by
  ``release.yml``.
- The PyPI job uses OIDC trusted publishing through ``uv publish``; no
  PyPI token should be stored in repository secrets for the normal path.

Maintainer Preflight
--------------------

Run these before merging a release PR or manually dispatching release
workflow diagnostics:

.. code:: bash

   uv sync --extra tests --extra typing
   uv run --with pip-audit==2.10.0 pip-audit --skip-editable
   uv run ruff check .
   uv run mypy src/extended_data
   uv run pytest
   uv run sphinx-build -W -E -b html docs docs/_build/html
   uv build

Workflow Hygiene
----------------

- Keep ``.github/workflows/*.yml`` actions pinned to exact commit SHAs.
- Update adjacent version comments when refreshing action SHAs.
- Use ``gh`` to verify latest stable action releases before changing
  pins.
- Keep top-level ``permissions: {}`` and grant only job-scoped
  permissions.

Current workflow action pins:

+--------------------------------------+-----------------------+----------------------------------------------+
| Action                               | Stable version        | Commit SHA                                   |
+======================================+=======================+==============================================+
| ``actions/checkout``                 | ``v7.0.0``            | ``9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0`` |
+--------------------------------------+-----------------------+----------------------------------------------+
| ``actions/configure-pages``          | ``v6.0.0``            | ``45bfe0192ca1faeb007ade9deae92b16b8254a0d`` |
+--------------------------------------+-----------------------+----------------------------------------------+
| ``actions/deploy-pages``             | ``v5.0.0``            | ``cd2ce8fcbc39b97be8ca5fce6e763baed58fa128`` |
+--------------------------------------+-----------------------+----------------------------------------------+
| ``actions/setup-python``             | ``v6.3.0``            | ``ece7cb06caefa5fff74198d8649806c4678c61a1`` |
+--------------------------------------+-----------------------+----------------------------------------------+
| ``actions/upload-pages-artifact``    | ``v5.0.0``            | ``fc324d3547104276b827a68afc52ff2a11cc49c9`` |
+--------------------------------------+-----------------------+----------------------------------------------+
| ``astral-sh/setup-uv``               | ``v8.2.0``            | ``fac544c07dec837d0ccb6301d7b5580bf5edae39`` |
+--------------------------------------+-----------------------+----------------------------------------------+
| ``googleapis/release-please-action`` | ``v5.0.0``            | ``45996ed1f6d02564a971a2fa1b5860e934307cf7`` |
+--------------------------------------+-----------------------+----------------------------------------------+

Publishing Flow
---------------

1. Land normal feature, fix, docs, and maintenance commits using
   Conventional Commit prefixes.
2. Let ``release.yml`` open or update the release-please PR.
3. Review the release PR for the expected changelog and manifest
   updates.
4. Merge the release PR.
5. Confirm ``release.yml`` created the GitHub release and dispatched
   ``cd.yml``.
6. Confirm ``cd.yml`` published to PyPI through trusted publishing and
   deployed the Sphinx site to GitHub Pages for ``extended-data.dev``.
7. Verify the package can be installed from PyPI:

.. code:: bash

   python -m pip install extended-data
   python -c "import extended_data; print(extended_data.__version__)"

Manual Repairs
--------------

Manual tags or PyPI uploads are repair paths, not the release process.
If a release workflow fails after release-please creates a tag:

1. Keep the failed tag intact while diagnosing unless the release is
   proven unrecoverable.
2. Prefer rerunning the failed workflow job.
3. If a bad GitHub release was published, delete only the bad artifacts
   needed for repair.
4. Document the repair in the PR or release notes.
