Workflows
=========

Tier 3 processors use primitives and containers to handle file, API, and
workflow boundaries.

DataFile
--------

.. code:: python

   from extended_data import DataFile, read_data_file

   artifact = DataFile.decode('{"service": {"name": "api"}}', suffix="json")
   print(artifact.data["service"]["name"].upper_first())
   print(artifact.metadata["encoding"])

   loaded = read_data_file("config/service.yaml")
   print(loaded["service"]["name"].upper_first())

``DataFile`` keeps source labels and metadata promoted and redacted
before they enter workflow step names or result metadata.

DataWorkflow
------------

.. code:: python

   from extended_data import DataWorkflow

   result = (
       DataWorkflow.from_file("config/base.yaml")
       .merge_file("config/dev.yaml", name="merge-dev")
       .transform("reconstruct", "unhump")
       .write("build/config.yaml")
   )

   print(result.steps)
   print(result.as_extended())
   print(result.as_builtin())

Data Sync
---------

.. code:: python

   from extended_data import DataWorkflow, sync_value_to_file

   direct = sync_value_to_file({"service": "api"}, "build/config.json", encoding="json")
   workflow = DataWorkflow.from_value({"service": "api"}).sync_file("build/config.yaml")

   print(direct.changed)
   print(workflow.to_dict()["destination"])

Sync primitives compare rendered output before writing. That gives
higher layers, such as ``vendor-fabric``, a base local file sync
operation without reimplementing export, redaction, and metadata
handling.

The CLI exposes the same data boundary:

.. code:: bash

   extended-data decode '{"service": {"name": "api"}}' --suffix json
   extended-data inspect --file config.yaml
   extended-data merge config/base.yaml config/dev.yaml --output yaml
   extended-data transform --file payload.json --step reconstruct --step unhump
