# Extended Data

`extended-data` is one Python distribution with one `extended_data` namespace
for pure data primitives, extended containers, file and workflow processors,
inputs, logging, and first-class vendor data integrations.

```bash
pip install extended-data
```

Optional integrations are installed by feature:

```bash
pip install "extended-data[aws,github,vault]"
pip install "extended-data[google,slack,zoom]"
pip install "extended-data[meshy,mcp]"
pip install "extended-data[ai]"
```

## Package Tiers

```text
extended_data/
  primitives/   pure functions, codecs, type coercion, redaction
  containers/   ExtendedString, ExtendedDict, ExtendedList, ExtendedTuple, ExtendedSet
  io/           file, import, export, and base64 processors
  inputs/       input loading and decorator-based injection
  logging/      structured lifecycle logging
  connectors/   external data integrations and ConnectorFabric
  secrets/      SecretSync pipeline bridge
  workflows/    higher-order data processing
```

The old `extended_data_types`, `directed_inputs_class`, `lifecyclelogging`, and
`vendor_connectors` namespaces are intentionally not shimmed in this major
version. Migration gaps should fail visibly.

```{toctree}
:caption: Guides
:maxdepth: 2

getting-started
core/primitives
core/containers
core/workflows
operations/inputs
operations/logging
integrations/connectors
integrations/secrets
examples/index
publishing
PUBLISHING_CHECKLIST
package-surface
```

```{toctree}
:caption: API Reference
:maxdepth: 2

api/index
```
