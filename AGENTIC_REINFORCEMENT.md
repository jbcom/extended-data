# Agentic Reinforcement

This file exists to stop boundary drift across the `ExtendedData` ->
`VendorData` -> `AgenticData` stack.

## Root Superclass

- `ExtendedData` is the root superclass and polymorphic factory.
- Downstream layers build on it; they do not replace it, fork it, or recreate
  its promotion rules.
- `ExtendedData(value)` remains the canonical way to promote built-in Python
  data into the most specific extended container shape.

## What This Repository Owns

- Tier 1 primitives
- Tier 2 extended containers
- Tier 3 generic file, import/export, workflow, sync, input, and logging
  primitives
- the stable base contract that downstream repos extend

## What This Repository Does Not Own

- provider activation or connector registries
- vendor capability dispatch
- SecretSync Go runtime, gopy binding source, or Python facade behavior
- runtime selection
- LangChain, CrewAI, LangGraph, Strands, or MCP agent adapters
- agent orchestration or agent-facing tool catalogs

## Downstream Contract

- `vendor-fabric` may extend `ExtendedData` with additive provider coordination.
- `agentic-fabric` may extend the vendor layer with additive runtime and agent
  behavior.
- If a proposed change here makes those downstream facade types harder to keep
  stable, treat that as a regression.

## Guardrails

- Do not add vendor-aware or agent-aware branching here.
- Do not move provider or runtime wrappers into this repo.
- Preserve `ExtendedData` factory semantics, shape promotion, and
  built-in-to-extended round-tripping.
- Keep docs and tests explicit about this repo being the base layer, not the
  vendor or agent layer.
