---
title: primitives.transformations.strings.inflection
description: Public API documentation generated from source.
---

# `primitives.transformations.strings.inflection`

```python
def pluralize(word: str, count: int | None = None) -> str:
def singularize(word: str) -> str:
def camelize(phrase: str, uppercase_first_letter: bool = True) -> str:
def underscore(phrase: str) -> str:
def humanize(phrase: str, capitalize: bool = True) -> str:
def titleize(phrase: str) -> str:
def ordinalize(value: int | str) -> str:
def parameterize(phrase: str, separator: str = "-") -> str:
```

## Source

[View source](https://github.com/jbcom/extended-data/blob/main/packages/extended-data/src/extended_data/primitives/transformations/strings/inflection.py)
