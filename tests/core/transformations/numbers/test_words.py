"""Tests for number word operations."""

from __future__ import annotations

import pytest

from extended_data.transformations.numbers import words as words_module
from extended_data.transformations.numbers.words import (
    fraction_to_words,
    number_to_words,
    ordinal_to_words,
    words_to_fraction,
    words_to_number,
    words_to_ordinal,
)


def test_number_to_words() -> None:
    """Test conversion of numbers to words."""
    assert number_to_words(0) == "zero"
    assert number_to_words(9) == "nine"
    assert number_to_words(19) == "nineteen"
    assert number_to_words(99) == "ninety-nine"
    assert number_to_words(100) == "one hundred"
    assert number_to_words(101) == "one hundred and one"
    assert number_to_words(999) == "nine hundred and ninety-nine"
    assert number_to_words(1000) == "one thousand"
    assert number_to_words(1000000) == "one million"

    # Test negative numbers
    assert number_to_words(-42) == "minus forty-two"

    # Test decimal numbers
    assert number_to_words(3.14) == "three point one four"
    assert number_to_words(-0.001) == "minus zero point zero zero one"

    # Test with different options
    assert number_to_words(42, capitalize=True) == "Forty-two"
    assert number_to_words(1042, conjunction="") == "one thousand forty-two"
    assert number_to_words(342, conjunction="plus") == "three hundred plus forty-two"

    # Test invalid input
    with pytest.raises(ValueError):
        number_to_words(float("inf"))
    with pytest.raises(ValueError):
        number_to_words(float("nan"))


def test_words_to_number() -> None:
    """Test conversion of words to numbers."""
    assert words_to_number("zero") == 0
    assert words_to_number("nine") == 9
    assert words_to_number("nineteen") == 19
    assert words_to_number("ninety-nine") == 99
    assert words_to_number("one hundred") == 100
    assert words_to_number("one hundred and one") == 101
    assert words_to_number("nine hundred and ninety-nine") == 999
    assert words_to_number("one thousand") == 1000
    assert words_to_number("one million") == 1000000

    # Test negative numbers
    assert words_to_number("minus forty-two") == -42

    # Test decimal numbers
    assert words_to_number("three point one four") == 3.14
    assert words_to_number("minus zero point zero zero one") == -0.001

    # Test with different formats
    assert words_to_number("Forty-Two") == 42
    assert words_to_number("one thousand forty-two") == 1042
    assert words_to_number("thousand") == 1000

    # Test invalid input
    with pytest.raises(ValueError):
        words_to_number("invalid")
    with pytest.raises(ValueError):
        words_to_number("")
    with pytest.raises(ValueError, match="digits after 'minus'"):
        words_to_number("minus")


def test_ordinal_to_words() -> None:
    """Test conversion of ordinal numbers to words."""
    assert ordinal_to_words(1) == "first"
    assert ordinal_to_words(2) == "second"
    assert ordinal_to_words(3) == "third"
    assert ordinal_to_words(4) == "fourth"
    assert ordinal_to_words(11) == "eleventh"
    assert ordinal_to_words(21) == "twenty-first"
    assert ordinal_to_words(100) == "one hundredth"
    assert ordinal_to_words(101) == "one hundred and first"

    # Test with different options
    assert ordinal_to_words(42, capitalize=True) == "Forty-second"

    # Test invalid input
    with pytest.raises(ValueError):
        ordinal_to_words(0)
    with pytest.raises(ValueError):
        ordinal_to_words(-1)
    with pytest.raises(TypeError):
        ordinal_to_words(1.5)  # type: ignore[arg-type]


def test_words_to_ordinal() -> None:
    """Test conversion of words to ordinal numbers."""
    assert words_to_ordinal("first") == 1
    assert words_to_ordinal("second") == 2
    assert words_to_ordinal("third") == 3
    assert words_to_ordinal("fourth") == 4
    assert words_to_ordinal("eleventh") == 11
    assert words_to_ordinal("twenty-first") == 21
    assert words_to_ordinal("one hundredth") == 100
    assert words_to_ordinal("one hundred and first") == 101

    # Test with different formats
    assert words_to_ordinal("Forty-second") == 42

    # Test invalid input
    with pytest.raises(ValueError):
        words_to_ordinal("zeroth")
    with pytest.raises(ValueError, match="positive integer"):
        words_to_ordinal("zero")
    with pytest.raises(ValueError):
        words_to_ordinal("invalid")
    with pytest.raises(ValueError):
        words_to_ordinal("")
    with pytest.raises(ValueError, match="cannot be negative"):
        words_to_ordinal("minus first")
    assert words_to_ordinal("twentieths") == 20
    assert words_to_ordinal("hundredths") == 100


def test_fraction_to_words() -> None:
    """Test conversion of fractions to words."""
    assert fraction_to_words("1/2") == "one half"
    assert fraction_to_words("1/4") == "one quarter"
    assert fraction_to_words("3/4") == "three quarters"
    assert fraction_to_words("2/3") == "two thirds"
    assert fraction_to_words("2/13") == "two thirteenths"

    # Test mixed numbers
    assert fraction_to_words("1 1/2") == "one and a half"
    assert fraction_to_words("2 3/4") == "two and three quarters"
    assert fraction_to_words("-3/2") == "minus one and a half"
    assert fraction_to_words("0/5") == "zero"

    # Test with different options
    assert fraction_to_words("1/2", capitalize=True) == "One half"

    # Test invalid input
    with pytest.raises(ValueError):
        fraction_to_words("0/0")
    with pytest.raises(ValueError):
        fraction_to_words("invalid")
    with pytest.raises(ValueError):
        fraction_to_words("")


def test_words_to_fraction() -> None:
    """Test conversion of words to fractions."""
    assert words_to_fraction("one half") == "1/2"
    assert words_to_fraction("one quarter") == "1/4"
    assert words_to_fraction("three quarters") == "3/4"
    assert words_to_fraction("two thirds") == "2/3"

    # Test mixed numbers
    assert words_to_fraction("one and a half") == "1 1/2"
    assert words_to_fraction("two and three quarters") == "2 3/4"
    assert words_to_fraction("minus one half") == "-1/2"
    assert words_to_fraction("minus five thirds") == "-1 2/3"
    assert words_to_fraction("two halves") == "1"
    assert words_to_fraction("five thirds") == "1 2/3"

    # Test with different formats
    assert words_to_fraction("One Half") == "1/2"

    # Test invalid input
    with pytest.raises(ValueError):
        words_to_fraction("invalid")
    with pytest.raises(ValueError):
        words_to_fraction("")
    with pytest.raises(ValueError, match="value after 'minus'"):
        words_to_fraction("minus")
    with pytest.raises(ValueError, match="fractional part"):
        words_to_fraction("one and")


def test_number_word_internal_helpers_cover_edge_paths() -> None:
    """Exercise internal parsing branches that public helpers pre-validate away."""
    with pytest.raises(ValueError, match="non-empty string"):
        words_module._NumberParser([]).number()
    with pytest.raises(ValueError, match="followed by digits"):
        words_module._NumberParser(["point"]).number()
    with pytest.raises(ValueError, match="Invalid decimal digit"):
        words_module._NumberParser(["one", "point", "ten"]).number()
    with pytest.raises(ValueError, match="Unrecognized number word"):
        words_module._NumberParser(["bogus"]).integer()

    assert words_module._replace_ordinals_with_cardinals(["thirds", "twentieths", "millionths", "plain"]) == [
        "three",
        "twenty",
        "million",
        "plain",
    ]
    assert words_module._replace_ordinals_with_cardinals(["twentieth"]) == ["twenty"]

    assert words_module._denominator_word(6, plural=True) == "sixths"

    def _mock_plural_denominator(*_args, **_kwargs) -> str:
        return "sixths"

    original_num2words = words_module.num2words
    words_module.num2words = _mock_plural_denominator  # type: ignore[assignment]
    try:
        assert words_module._denominator_word(6, plural=True) == "sixths"
    finally:
        words_module.num2words = original_num2words  # type: ignore[assignment]
    assert words_module._denominator_from_word("halves") == 2
    assert words_module._denominator_from_word("quarters") == 4
    with pytest.raises(ValueError, match="Unrecognized denominator word"):
        words_module._denominator_from_word("bogus")

    with pytest.raises(TypeError, match="must be a string"):
        words_module._parse_fraction_string(3.14)
    assert words_module._parse_fraction_string("3 / 4") == words_module.Fraction(3, 4)
