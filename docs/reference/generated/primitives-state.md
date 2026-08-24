---
title: primitives.state
description: Public API documentation generated from source.
---

# `primitives.state`

```python
def is_nothing(v: Any) -> bool:
def are_nothing(*args: Any, **kwargs: Any) -> bool:
def all_non_empty(*args: Any, **kwargs: Any) -> list[Any] | dict[str, Any] | tuple[list[Any], dict[str, Any]] | None:
def all_non_empty_in_list(input_list: list[Any]) -> list[Any]:
def all_non_empty_in_dict(input_dict: dict[Any, Any]) -> dict[Any, Any]:
def first_non_empty(*vals: Any) -> Any:
def any_non_empty(m: dict[Any, Any], *keys: Any) -> dict[Any, Any]:
def yield_non_empty(m: dict[Any, Any], *keys: Any) -> Generator[dict[Any, Any], None, None]:
```

## Source

[View source](https://github.com/jbcom/extended-data/blob/main/packages/extended-data/src/extended_data/primitives/state.py)
