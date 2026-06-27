# Changelog

## [8.0.0](https://github.com/jbcom/extended-data/compare/extended-data-v7.0.0...extended-data-v8.0.0) (2026-06-26)


### ⚠ BREAKING CHANGES

* extended-data now ships only the base data primitives, containers, IO, inputs, logging, and workflow surfaces. Vendor integrations, Python-native SecretSync, and agent-facing wrappers move to vendor-fabric.
* clean integrated package surface ([#2](https://github.com/jbcom/extended-data/issues/2))

### Features

* add generic connector fabric lookup ([138ebf5](https://github.com/jbcom/extended-data/commit/138ebf5269811cda5f0109124801f85c9ae9ac18))
* expose integrated root API ([#4](https://github.com/jbcom/extended-data/issues/4)) ([7e5862f](https://github.com/jbcom/extended-data/commit/7e5862fa1764789c55e4062e965aa1d184470578))
* move connector surfaces out of extended-data ([0495d8b](https://github.com/jbcom/extended-data/commit/0495d8b1f1441b3819a77c6c2bfe2af38a78a38e))


### Code Refactoring

* clean integrated package surface ([#2](https://github.com/jbcom/extended-data/issues/2)) ([76c7a3d](https://github.com/jbcom/extended-data/commit/76c7a3d594396fee9ae599e80c84e35590f5ae6a))

## 7.0.0 (2026-06-10)

### Features

- Consolidate the previous Extended Data Python libraries into the single
  `extended-data` distribution and `extended_data` namespace.
- Promote data utilities, inputs, logging, connectors, secrets adapters, and
  workflow placeholders as first-class package members.
