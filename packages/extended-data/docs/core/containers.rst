Containers
==========

Tier 2 wraps Python data shapes with shape-specific ``ExtendedString``,
``ExtendedDict``, ``ExtendedList``, ``ExtendedTuple``, and
``ExtendedSet`` containers. ``ExtendedData`` is their common root and
polymorphic constructor: callers can use one entrypoint while still
receiving the concrete extended type for the incoming value.

Construction and mutation promote nested values, so method chains
survive normal Python literals.

.. code:: python

   from extended_data import ExtendedData, ExtendedDict, ExtendedList, ExtendedString

   payload = ExtendedDict({"service": {"name": "api"}, "tags": ["api", "api", ""]})
   generic = ExtendedData(payload).merge({"service": {"enabled": True}})

   print(payload["service"]["name"].upper_first())
   print(generic.as_builtin()["service"]["enabled"])
   print(payload["tags"].compact().deduplicate())
   print(ExtendedString("HTTP Response Value").to_snake_case())

Polymorphic ExtendedData
------------------------

Use ``ExtendedData`` at file, API, workflow, and vendor boundaries where
the payload may be a mapping today, a list tomorrow, or a scalar status
value from a different provider. The constructor returns the concrete
extended subtype when one applies, so normal Python collection behavior
remains native rather than proxied.

.. code:: python

   from extended_data import ExtendedData, ExtendedDict, ExtendedList, ExtendedString

   vendor = ExtendedData({"vendor": "google", "payload": {"names": ["alpha"]}})
   vendor["enabled"] = "true"

   assert type(vendor) is ExtendedDict
   assert isinstance(vendor, ExtendedData)
   assert vendor.shape == "mapping"
   assert vendor.get("vendor").upper_first() == "Google"
   assert vendor["payload"]["names"][0].upper_first() == "Alpha"

   merged = vendor.merge({"payload": {"region": "us-east-1"}})
   assert merged.as_builtin()["payload"]["region"] == "us-east-1"

   assert type(ExtendedData([{"name": "api"}]).append({"name": "worker"})) is ExtendedList
   assert type(ExtendedData("HTTP Response Value")) is ExtendedString

The common root exposes broad shape predicates without forcing dict-only
code paths:

.. code:: python

   assert ExtendedData("HTTP Response Value").is_string
   assert ExtendedData([{"name": "api"}]).is_sequence
   assert ExtendedData({"prod", "api"}).is_set
   assert ExtendedData(42).is_scalar
   assert ExtendedData().is_none

Downstream packages can subclass ``ExtendedData`` for additive facades
without being collapsed by the root factory. Store the promoted payload
with ``ExtendedData(value)`` and keep provider or runtime behavior on the
subclass:

.. code:: python

   class ProviderData(ExtendedData):
       def __init__(self, value, *, provider):
           self.provider = provider
           self._data = ExtendedData(value)

       @property
       def value(self):
           return self._data

   provider_data = ProviderData({"service": {"name": "api"}}, provider="vendor")

   assert type(provider_data) is ProviderData
   assert provider_data.shape == "mapping"
   assert provider_data["service"]["name"].upper_first() == "Api"

Facades that need to keep the same outer identity while changing shape
should override ``cast()`` and replace their internal ``ExtendedData``
value.

It also provides shared data-boundary helpers:

.. code:: python

   decoded = ExtendedData.decode('{"service": {"name": "api"}}', suffix="json")
   loaded = ExtendedData.read("config/service.yaml")
   result = loaded.sync_to_file("build/service.json", encoding="json")

   assert decoded["service"]["name"].upper_first() == "Api"
   print(result.changed)

Promotion and Lowering
----------------------

.. code:: python

   from extended_data import extend_data, to_builtin

   data = extend_data({"outer": {"inner": ["api"]}})
   assert data["outer"]["inner"][0].upper_first() == "Api"

   plain = to_builtin(data)
   assert plain == {"outer": {"inner": ["api"]}}

Tuples remain tuple-shaped when promoted and lowered. Sets stay
set-shaped. Mapping keys are lowered before export so JSON, YAML, TOML,
and HCL encoders can hand data to their underlying format libraries
safely.
