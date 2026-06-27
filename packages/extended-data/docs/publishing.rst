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
5. ``release.yml`` dispatches package-specific CD with the release tag:
   ``cd.yml`` for ``extended-data`` and
   ``cd-pytest-extended-data.yml`` for ``pytest-extended-data``.
6. The package CD workflow publishes to PyPI with OIDC trusted
   publishing. ``extended-data`` releases also deploy the Sphinx/Furo
   docs site.

PyPI Trusted Publishers
-----------------------

Each published package needs a PyPI trusted publisher matching the
workflow that uploads it. ``extended-data`` uses the existing
``cd.yml`` publisher. The first ``pytest-extended-data`` publish needs a
PyPI pending publisher with these values before rerunning CD:

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
     - ``cd-pytest-extended-data.yml``
   * - Environment
     - leave blank

After the pending publisher exists, rerun the failed publish with:

.. code:: bash

   gh workflow run cd-pytest-extended-data.yml --ref main -f tag=pytest-extended-data-v0.1.0

Package-scoped release-please configuration owns package versions,
package changelogs, release tags, and the release manifest. Do not add
the root ``uv.lock`` as a package ``extra-files`` target; normal
``uv sync`` setup can refresh the workspace lock locally, while package
builds publish from each package's committed metadata.

Manual tags and manual PyPI uploads are repair paths, not the normal
release process.
