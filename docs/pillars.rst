Pillars
========

These pillars define what belongs in ``extended-data``.

Pure Data First
---------------

Tier 1 primitives are plain Python functions. They should be
deterministic, easy to test, and independent of files, logging state,
vendors, agent runtimes, network clients, or environment configuration.

Real Python Containers
----------------------

Tier 2 containers are real Python objects with the closest native
behavior for their shape. ``ExtendedString``, ``ExtendedDict``,
``ExtendedList``, ``ExtendedTuple``, and ``ExtendedSet`` inherit from
``ExtendedData`` and from the appropriate Python base.

Promote On Boundaries
---------------------

Data entering the package should be promoted into extended containers.
Nested writes should keep promoting incoming built-in values. Data
leaving the package should cross explicit boundaries such as
``as_builtin()``, ``to_export_safe()``, file writes, workflow results,
or sync operations.

Compose Higher Layers
---------------------

Tier 3 features compose Tier 1 and Tier 2. File processing, input
loading, logging snapshots, imports, exports, and workflows should use
shared data primitives instead of reimplementing merge, redaction,
encoding, coercion, or promotion behavior.

Keep Vendors Out
----------------

Vendor clients, cloud SDKs, agent runtimes, and live API sync behavior
do not belong in ``extended-data``.

No Compatibility Shims
----------------------

This package is a clean major-version surface. Removed package names and
removed in-package connector namespaces should fail to import. Breakage
is preferable to silently carrying stale contracts.

Docs And Tests Together
-----------------------

Public behavior must be backed by tests and docs in the same change.
Examples are executable contracts. Sphinx/Furo docs, autodoc2 API
output, README guidance, unit tests, and release hygiene checks all need
to agree.
