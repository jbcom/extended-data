---
title: primitives.formats.yaml.representers
description: Public API documentation generated from source.
---

# `primitives.formats.yaml.representers`

```python
def yaml_represent_tagged(dumper: SafeDumper, data: YamlTagged) -> Node:
def yaml_represent_pairs(dumper: SafeDumper, data: YamlPairs) -> MappingNode:
def yaml_str_representer(dumper: SafeDumper, data: str) -> ScalarNode:
def yaml_literal_str_representer(dumper: SafeDumper, data: LiteralScalarString) -> ScalarNode:
```

## Source

[View source](https://github.com/jbcom/extended-data/blob/main/packages/extended-data/src/extended_data/primitives/formats/yaml/representers.py)
