#!/usr/bin/env python3
"""String transformation examples for Extended Data core library.

This module demonstrates case conversion, humanization, pluralization,
and other string manipulation utilities provided by the library.
"""

from __future__ import annotations

from extended_data import (
    humanize,
    ordinalize,
    pluralize,
    singularize,
    titleize,
    to_camel_case,
    to_kebab_case,
    to_pascal_case,
    to_snake_case,
)


def demonstrate_case_conversion() -> None:
    """Demonstrate case conversion utilities."""
    examples = [
        "hello_world",
        "my-variable-name",
        "SomeClassName",
        "user_account_settings",
    ]

    print("=== Case Conversion ===\n")

    print("-- to_camel_case --")
    for text in examples:
        print(f"  to_camel_case({text!r}) -> {to_camel_case(text)!r}")

    print("\n-- to_pascal_case --")
    for text in examples:
        print(f"  to_pascal_case({text!r}) -> {to_pascal_case(text)!r}")

    print("\n-- to_snake_case --")
    for text in examples:
        print(f"  to_snake_case({text!r}) -> {to_snake_case(text)!r}")

    print("\n-- to_kebab_case --")
    for text in examples:
        print(f"  to_kebab_case({text!r}) -> {to_kebab_case(text)!r}")

    print()


def demonstrate_humanization() -> None:
    """Demonstrate string humanization."""
    examples = [
        "user_id",
        "createdAt",
        "HTTPResponse",
        "employee_salary_amount",
    ]

    print("=== Humanization ===\n")

    print("-- humanize --")
    for example in examples:
        print(f"  humanize({example!r}) -> {humanize(example)!r}")

    print("\n-- titleize --")
    for example in examples:
        print(f"  titleize({example!r}) -> {titleize(example)!r}")

    print()


def demonstrate_pluralization() -> None:
    """Demonstrate pluralization and singularization."""
    words = ["cat", "child", "person", "mouse", "analysis", "octopus"]

    print("=== Pluralization ===\n")

    print("-- pluralize --")
    for word in words:
        print(f"  pluralize({word!r}) -> {pluralize(word)!r}")

    print("\n-- singularize --")
    plural_words = ["cats", "children", "people", "mice", "analyses", "octopi"]
    for word in plural_words:
        print(f"  singularize({word!r}) -> {singularize(word)!r}")

    print()


def demonstrate_ordinalization() -> None:
    """Demonstrate number ordinalization."""
    numbers = [1, 2, 3, 4, 11, 12, 13, 21, 22, 23, 100, 101, 102, 103]

    print("=== Ordinalization ===\n")

    for num in numbers:
        print(f"  ordinalize({num}) -> {ordinalize(num)!r}")

    print()


if __name__ == "__main__":
    demonstrate_case_conversion()
    demonstrate_humanization()
    demonstrate_pluralization()
    demonstrate_ordinalization()
