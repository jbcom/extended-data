# Extended Data

`extended-data` is one Python distribution with one `extended_data` namespace
for pure data primitives, extended containers, file and workflow processors,
inputs, and structured logging.

```bash
pip install extended-data
```

External API clients live in the separate `vendor-fabric` distribution.
Vendor-backed Python sync and agent workflows also live in `vendor-fabric`.

## Package Tiers

```text
extended_data/
  containers/   ExtendedData plus ExtendedString/Dict/List/Tuple/Set
  inputs/       input loading and decorator-based injection
  io/           file, import, export, and base64 processors
  logging/      structured lifecycle logging
  primitives/   pure functions, codecs, type coercion, redaction
  workflows/    higher-order data processing
```

The old `extended_data_types`, `directed_inputs_class`, and `lifecyclelogging`
package names are intentionally not shimmed in this major version. The removed
`extended_data.connectors` and `extended_data.secrets` namespaces are also not
preserved.

```{toctree}
:caption: Guides
:maxdepth: 2

getting-started
core/primitives
core/containers
core/workflows
operations/inputs
operations/logging
examples/index
publishing
PUBLISHING_CHECKLIST
package-surface
ownership-map
```

```{toctree}
:caption: API Reference
:maxdepth: 2

api/index
```
