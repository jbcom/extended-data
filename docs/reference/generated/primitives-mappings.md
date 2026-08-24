---
title: primitives.mappings
description: Public API documentation generated from source.
---

# `primitives.mappings`

```python
def deep_merge(*mappings: Mapping[str, Any]) -> dict[str, Any]:
def create_merger(
def first_non_empty_value_from_map(m: Mapping[str, Any], *keys: str) -> Any:
def deduplicate_map(m: Mapping[str, Any]) -> dict[str, Any]:
def all_values_from_map(m: Mapping[str, Any]) -> list[Any]:
def flatten_map(
def zipmap(a: list[str], b: list[str]) -> dict[str, str]:
class SortedDefaultDict(defaultdict[KT, VT], SortedDict[KT, VT]):  # type: ignore[misc]
def get_default_dict(
def unhump_map(
def filter_map(
```

## Source

[View source](https://github.com/jbcom/extended-data/blob/main/packages/extended-data/src/extended_data/primitives/mappings.py)
