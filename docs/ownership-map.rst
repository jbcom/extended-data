Ownership Map
=============

``extended-data`` owns the base data layer. Surfaces outside that
boundary were moved into repositories where their dependencies, docs,
tests, and release cadence are first-class.

In This Package
---------------

+-----------------------------------+-----------------------------------+
| Surface                           | Current owner                     |
+===================================+===================================+
| Pure data functions               | ``extended_data.primitives``      |
+-----------------------------------+-----------------------------------+
| Generic and shape-specific        | ``extended_data.containers``      |
| extended containers               |                                   |
+-----------------------------------+-----------------------------------+
| File import/export and codecs     | ``extended_data.io``              |
+-----------------------------------+-----------------------------------+
| Workflow composition and local    | ``extended_data.workflows``       |
| file sync primitives              |                                   |
+-----------------------------------+-----------------------------------+
| Input loading and decorators      | ``extended_data.inputs``          |
+-----------------------------------+-----------------------------------+
| Structured lifecycle logging      | ``extended_data.logging``         |
+-----------------------------------+-----------------------------------+

Moved Out
---------

+-----------------------+-------------------------+------------------------------------+
| Prior surface         | Current repository      | Install target                     |
+=======================+=========================+====================================+
| External vendor API   | ``jbcom/vendor-fabric`` | ``vendor-fabric``                  |
| clients               |                         |                                    |
+-----------------------+-------------------------+------------------------------------+
| Vendor fabric MCP and | ``jbcom/vendor-fabric`` | ``vendor-fabric[...]``             |
| tool adapters         |                         |                                    |
+-----------------------+-------------------------+------------------------------------+
| Meshy, Slack, Google, | ``jbcom/vendor-fabric`` | ``vendor-fabric[...]``             |
| GitHub, AWS, Vault,   |                         |                                    |
| Zoom, Anthropic,      |                         |                                    |
| Cursor integrations   |                         |                                    |
+-----------------------+-------------------------+------------------------------------+
| Vendor-backed Python  | ``jbcom/vendor-fabric`` | ``vendor-fabric[secrets-sync]``    |
| sync capabilities     |                         |                                    |
+-----------------------+-------------------------+------------------------------------+
| SecretSync agent tool | ``jbcom/vendor-fabric`` | ``vendor-fabric[ai,secrets-sync]`` |
| wrappers              |                         |                                    |
+-----------------------+-------------------------+------------------------------------+
| Agent framework       | ``jbcom/vendor-fabric`` | ``vendor-fabric[ai]``              |
| integrations          |                         |                                    |
+-----------------------+-------------------------+------------------------------------+

The old in-package connector and secrets namespaces are intentionally
absent. That is a clean major-version boundary: code should depend on
the package that owns the capability it uses.

Dependency Direction
--------------------

The intended layering is dependency-inward:

.. code:: text

   extended-data
     <- vendor-fabric

``extended-data`` has no dependency on the higher layers. Higher layers
may use ``extended-data`` primitives, containers, input handling,
workflows, and logging without reimplementing those base concerns.
