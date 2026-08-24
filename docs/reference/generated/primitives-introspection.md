---
title: primitives.introspection
description: Public API documentation generated from source.
---

# `primitives.introspection`

```python
def get_caller() -> str:
def get_unique_signature(obj: Any, delim: str = "/") -> str:
def filter_methods(methods: list[str]) -> list[str]:
def get_available_methods(cls: builtins.type[Any]) -> dict[str, str | None]:
def get_inputs_from_docstring(docstring: str) -> dict[str, dict[str, str]]:
def update_docstring(original_docstring: str, new_inputs: dict[str, dict[str, str]]) -> str:
def current_python_version_is_at_least(minor: int, major: int = 3) -> bool:
```

## Source

[View source](https://github.com/jbcom/extended-data/blob/main/packages/extended-data/src/extended_data/primitives/introspection.py)
