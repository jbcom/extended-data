Architecture Plan
=================

This page records the local implementation plan for ``extended-data``.
It is the source of truth for this repository and intentionally avoids
owning downstream vendor or agent implementation details.

Boundary
--------

``extended-data`` is a Python-only package with one public namespace:
``extended_data``.

This package owns generic data behavior:

- pure data primitives
- extended data containers
- file import/export and decoding
- workflow composition
- input loading
- structured logging
- local sync primitives

This package does not own vendor SDKs, cloud connectors, SecretSync
provider behavior, agent runtimes, or agent framework adapters.

Package Tiers
-------------

The package has three tiers.

Tier 1 contains pure functions. These functions do not know about
logging, inputs, files, vendors, network clients, or agent frameworks.
They live under ``extended_data.primitives`` and cover serialization,
codecs, strings, maps, sequences, type coercion, redaction, matching,
and state helpers.

Tier 2 contains data containers. ``ExtendedData`` is the common
superclass and polymorphic constructor. ``ExtendedString``,
``ExtendedDict``, ``ExtendedList``, ``ExtendedTuple``, and
``ExtendedSet`` inherit from ``ExtendedData`` and the closest Python
collection base for their shape.

Tier 3 contains higher-order processors. Files, imports, exports,
workflows, input loading, and structured logging use Tier 1 and Tier 2
rather than reimplementing those primitives.

ExtendedData Superclass
-----------------------

``ExtendedData`` has two jobs:

1. It is the common base class for every extended container.
2. It is the polymorphic constructor for incoming data.

Calling ``ExtendedData(value)`` returns the best extended shape for
``value``:

.. code:: python

   from extended_data import ExtendedData, ExtendedDict, ExtendedList, ExtendedString

   assert type(ExtendedData({"name": "api"})) is ExtendedDict
   assert type(ExtendedData(["api"])) is ExtendedList
   assert type(ExtendedData("api")) is ExtendedString
   assert isinstance(ExtendedData({"name": "api"}), ExtendedData)

The shape-specific classes are real Python objects, not a detached proxy
facade. That keeps normal operations such as item access, list append,
set update, tuple concatenation, and string transforms direct and
testable.

Mutation And Casts
------------------

Python does not safely support mutating a single existing object between
unrelated built-in layouts, such as changing the same object from
mapping-shaped storage to string-shaped storage.

The package therefore uses this contract:

- shape-specific containers mutate in place for native mutable
  operations
- nested writes promote incoming values back into extended containers
- ``ExtendedData.cast(value)`` returns ``ExtendedData(value)``
- callers that need a different shape bind the returned object

.. code:: python

   data = ExtendedData({"service": {"name": "api"}})
   data["service"]["tags"] = ["edge"]

   assert type(data["service"]["tags"]) is ExtendedList

   data = data.cast("completed")

   assert type(data) is ExtendedString

Higher-order packages that must keep a stable outer identity can
override ``cast()`` locally by storing an internal ``ExtendedData``
value. That pattern belongs in those downstream repositories, not here.

Data Boundaries
---------------

Data entering this package should be promoted once, then remain extended
through normal mutations. Data leaving the package should cross explicit
boundaries:

- ``as_builtin()``
- ``as_extended()``
- ``to_export_safe()``
- ``wrap_for_export()``
- file writes
- workflow results
- sync results

Implicit compatibility shims should not be added for old package names
or removed connector namespaces.

Logging And Diagnostics
-----------------------

Tier 3 code should use ``extended_data.logging.Logging`` when a consumer
has configured it. Shared library code should otherwise use Python
warnings, exceptions, and logging primitives. Runtime library code
should not print outside CLI and example code.

Downstream Contract
-------------------

Downstream repositories build on this package:

- ``vendor-fabric`` extends ``ExtendedData`` with ``VendorData`` and
  provider capability routing.
- ``agentic-fabric`` extends the stack with ``AgenticData`` and
  agent/runtime capability routing.

Their implementation plans live in their own repositories.

Validation Contract
-------------------

Every public behavior needs tests and docs in the same change:

- unit tests for Tier 1 pure functions
- container tests for native operation behavior and nested promotion
- workflow and file tests for Tier 3 composition
- example contract tests for public examples
- release hygiene tests for action pinning, publishing, package surface,
  and removed namespace boundaries
- Sphinx/Furo documentation with autodoc2 API output
- tox environments for Python 3.11, 3.12, 3.13, and 3.14

``skip_missing_interpreters`` must stay disabled.
