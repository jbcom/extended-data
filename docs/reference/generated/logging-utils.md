---
title: logging.utils
description: Public API documentation generated from source.
---

# `logging.utils`

```python
def get_log_level(level: int | str) -> int:
def get_loggers() -> list[logging.Logger]:
def find_logger(name: str) -> logging.Logger | None:
def clear_existing_handlers(logger: logging.Logger) -> None:
def sanitize_json_data(data: Any) -> Any:
def add_labeled_json(
def add_unlabeled_json(
def add_json_data(
```

## Source

[View source](https://github.com/jbcom/extended-data/blob/main/packages/extended-data/src/extended_data/logging/utils.py)
