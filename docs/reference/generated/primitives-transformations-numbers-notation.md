---
title: primitives.transformations.numbers.notation
description: Public API documentation generated from source.
---

# `primitives.transformations.numbers.notation`

```python
def to_roman(number: int, *, upper: bool = True) -> str:
def from_roman(numeral: str) -> int:
def to_ordinal(number: int, *, words: bool = False) -> str:
def from_ordinal(text: str) -> int:
def to_words(number: float, *, capitalize: bool = False, conjunction: str = " and ") -> str:
def from_words(text: str) -> float:
def to_fraction(number: float, *, mixed: bool = False, precision: int | None = None) -> str:
def from_fraction(value: str) -> float:
```

## Source

[View source](https://github.com/jbcom/extended-data/blob/main/packages/extended-data/src/extended_data/primitives/transformations/numbers/notation.py)
