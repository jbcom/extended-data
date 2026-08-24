---
title: primitives.types
description: Public API documentation generated from source.
---

# `primitives.types`

```python
class ConversionError(ValueError):
def string_to_bool(val: str | bool | None, raise_on_error: bool = False) -> bool | None:
def string_to_float(val: str, raise_on_error: bool = False) -> float | None:
def string_to_int(val: str, raise_on_error: bool = False) -> int | None:
def string_to_path(val: str | bytes | os.PathLike[str] | None, raise_on_error: bool = False) -> Path | None:
def string_to_date(val: str, raise_on_error: bool = False) -> datetime.date | None:
def string_to_datetime(val: str, raise_on_error: bool = False) -> datetime.datetime | None:
def string_to_time(val: str, raise_on_error: bool = False) -> datetime.time | None:
def get_default_value_for_type(input_type: builtins.type[Any]) -> Any:
def get_primitive_type_for_instance_type(value: Any) -> builtins.type[Any]:
def typeof(item: Any, primitive_only: bool = False) -> builtins.type[Any]:
def convert_special_type(obj: Any) -> Any:
def convert_special_types(obj: Any) -> Any:
def is_potential_yaml(obj: str) -> bool:
def is_potential_json(obj: str) -> bool:
def reconstruct_special_type(converted_obj: str, fail_silently: bool = False) -> Any:
def reconstruct_special_types(obj: Any, fail_silently: bool = False) -> Any:
```

## Source

[View source](https://github.com/jbcom/extended-data/blob/main/packages/extended-data/src/extended_data/primitives/types.py)
