# SecretSync Alignment

This file locks the intended SecretSync boundary from the base data layer.

## Canonical Stack

1. `secrets-sync` owns the Go pipeline runtime, CLI, GitHub Action, deployment
   artifacts, and the gopy binding source consumed from Python.
2. `vendor-fabric` owns the Python facade over those bindings, plus credential
   handoff, provider coordination, and `ExtendedData` integration.
3. `agentic-fabric` owns framework-specific tool wrapping and runtime
   orchestration on top of `VendorData`.
4. `extended-data` stays the generic base layer underneath all of them.

## Binding Contract

- PyPI distribution: `secrets-sync-python-binding`
- Python import/module: `secrets_sync`
- `extended-data` should stay agnostic to that binding and only provide generic
  primitives that the downstream facade layers can reuse.

## This Repository's Role

- Provide generic containers, promotion, redaction, file IO, workflow, and
  logging primitives that SecretSync-adjacent repos can reuse.
- Stay ignorant of specific SecretSync providers, runtime invocation, gopy
  wiring, and agent framework concerns.

## Allowed Changes

- Add generic primitives that happen to help SecretSync, but only when they are
  broadly useful outside SecretSync.
- Keep `ExtendedData` promotion and built-in round-tripping stable so
  `VendorData` and `AgenticData` can safely compose on top.

## Forbidden Drift

- Do not add SecretSync-specific runtime policy here.
- Do not add vendor credential handoff or binding invocation here.
- Do not absorb provider or agent wrapper behavior because another repo is
  temporarily incomplete.
