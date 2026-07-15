# Changelog

## [8.4.3](https://github.com/jbcom/extended-data/compare/extended-data-v8.4.2...extended-data-v8.4.3) (2026-07-15)


### Bug Fixes

* align setup-uv publishing checklist pin ([2d08b45](https://github.com/jbcom/extended-data/commit/2d08b4567a80052b09b6f9457678b9c882d036d5))
* restore extended-data release hygiene ([4207aec](https://github.com/jbcom/extended-data/commit/4207aecd639c4390098ccd6d61d42fc79b365282))

## [8.4.2](https://github.com/jbcom/extended-data/compare/extended-data-v8.4.1...extended-data-v8.4.2) (2026-06-27)


### Bug Fixes

* close doc, autodoc2, and test coverage gaps ([#30](https://github.com/jbcom/extended-data/issues/30)) ([9c577df](https://github.com/jbcom/extended-data/commit/9c577df4e68c0ace888566a981f6054806b0da75))

## [8.4.1](https://github.com/jbcom/extended-data/compare/extended-data-v8.4.0...extended-data-v8.4.1) (2026-06-27)


### Bug Fixes

* stabilize ExtendedData subclass factory reentry ([#28](https://github.com/jbcom/extended-data/issues/28)) ([9a0fce5](https://github.com/jbcom/extended-data/commit/9a0fce5dad766be5b4c7445c6a42cf67b4183040))

## [8.4.0](https://github.com/jbcom/extended-data/compare/extended-data-v8.3.1...extended-data-v8.4.0) (2026-06-27)


### Features

* split extended data workspace packages ([5d49998](https://github.com/jbcom/extended-data/commit/5d4999836ff5c42faf1c9082e014a85d266845e4))

## [8.3.1](https://github.com/jbcom/extended-data/compare/extended-data-v8.3.0...extended-data-v8.3.1) (2026-06-27)


### Bug Fixes

* stabilize ExtendedData factory initialization ([e2b785f](https://github.com/jbcom/extended-data/commit/e2b785fe513097c9c4ac22fe7be9734f0c442fbb))

## [8.3.0](https://github.com/jbcom/extended-data/compare/extended-data-v8.2.0...extended-data-v8.3.0) (2026-06-27)


### Features

* make ExtendedData the polymorphic container root ([217d8d7](https://github.com/jbcom/extended-data/commit/217d8d7694d26b75c8a0e65979f5b8162a33be9f))

## [8.2.0](https://github.com/jbcom/extended-data/compare/extended-data-v8.1.0...extended-data-v8.2.0) (2026-06-27)


### Features

* make ExtendedData the generic data boundary ([030a475](https://github.com/jbcom/extended-data/commit/030a475644e5603b6624991b725e0294511f9b3c))

## [8.1.0](https://github.com/jbcom/extended-data/compare/extended-data-v8.0.0...extended-data-v8.1.0) (2026-06-27)


### Features

* add generic data facade and sync primitives ([daf4db8](https://github.com/jbcom/extended-data/commit/daf4db8d6bd681af285084380742cb492cc1a2b7))

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
