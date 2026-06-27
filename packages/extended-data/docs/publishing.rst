Publishing
==========

The workspace uses release-please, GitHub Releases, and PyPI trusted
publishing. The root workspace is not published. ``extended-data`` and
``pytest-extended-data`` are released from their package paths.

Local Gates
-----------

.. code:: bash

   tox -e lint,typecheck,audit,py311,py312,py313,py314,examples,docs,build

Release Flow
------------

1. Merge feature, fix, docs, and maintenance commits to ``main``.
2. ``release.yml`` runs release-please and opens or updates package
   release PRs.
3. Merge the release PR.
4. release-please creates the GitHub release and version tag.
5. ``release.yml`` dispatches ``cd.yml`` with the release tag and
   package name.
6. ``cd.yml`` publishes the selected package to PyPI with OIDC trusted
   publishing. ``extended-data`` releases also deploy the Sphinx/Furo
   docs site.

PyPI Trusted Publishers
-----------------------

Each published package needs a PyPI trusted publisher matching the
workflow that uploads it. Both ``extended-data`` and
``pytest-extended-data`` publish through the standard ``cd.yml``
workflow. If a new package needs an initial PyPI pending publisher, use
these values before rerunning CD:

.. list-table::
   :header-rows: 1

   * - Field
     - Value
   * - PyPI project
     - ``pytest-extended-data``
   * - GitHub owner
     - ``jbcom``
   * - GitHub repository
     - ``extended-data``
   * - Workflow filename
     - ``cd.yml``
   * - Environment
     - leave blank

After the pending publisher exists, rerun the failed publish with:

.. code:: bash

   gh workflow run cd.yml --ref main -f tag=pytest-extended-data-v0.1.0 -f package=pytest-extended-data

Package-scoped release-please configuration owns package versions,
package changelogs, release tags, and the release manifest. Do not add
the root ``uv.lock`` as a package ``extra-files`` target; normal
``uv sync`` setup can refresh the workspace lock locally, while package
builds publish from each package's committed metadata.

Manual tags and manual PyPI uploads are repair paths, not the normal
release process.
