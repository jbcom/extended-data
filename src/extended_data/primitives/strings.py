"""This module provides utilities for string manipulation and validation.

It includes functions to sanitize keys, truncate messages, manipulate character
cases, validate URLs, convert camelCase to TitleCase, and convert string representations
of truth to boolean values.
"""

from __future__ import annotations

from urllib.parse import urlparse

import inflection


def bytes_to_string(value: object) -> str:
    """Convert bytes, memoryview, bytearray, or another object to a string.

    Bytes-like values are decoded as UTF-8. Strings are returned unchanged and
    all other objects use their standard string representation.

    Args:
        value: The value to convert.

    Returns:
        The string representation of the input.

    Raises:
        UnicodeDecodeError: If the bytes or bytearray cannot be decoded into a valid UTF-8 string.
    """
    if isinstance(value, str):
        return value

    if isinstance(value, memoryview):
        value = value.tobytes()

    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8")

    return str(value)


def sanitize_key(key: str, delim: str = "_") -> str:
    """Sanitizes a key by replacing non-alphanumeric characters with a delimiter.

    Args:
        key (str): The key to sanitize.
        delim (str): The delimiter to replace non-alphanumeric characters with. Defaults to "_".

    Returns:
        str: The sanitized key.
    """
    key = str(key)
    return "".join(x if (x.isalnum() or x == delim) else delim for x in key)


def truncate(msg: str, max_length: int, ender: str = "...") -> str:
    """Truncates a message to a maximum length, appending an ender if truncated.

    Args:
        msg (str): The message to truncate.
        max_length (int): The maximum length of the truncated message.
        ender (str): The string to append to the truncated message. Defaults to "...".

    Returns:
        str: The truncated message.
    """
    msg = str(msg)
    ender = str(ender)
    if max_length <= 0:
        return ""

    if len(msg) <= max_length:
        return msg
    if len(ender) >= max_length:
        return ender[0] if ender else ""
    return msg[: max_length - len(ender)] + ender


def lower_first_char(inp: str) -> str:
    """Converts the first character of a string to lowercase.

    Args:
        inp (str): The input string.

    Returns:
        str: The string with the first character in lowercase.
    """
    inp = str(inp)
    return inp[:1].lower() + inp[1:] if inp else ""


def upper_first_char(inp: str) -> str:
    """Converts the first character of a string to uppercase.

    Args:
        inp (str): The input string.

    Returns:
        str: The string with the first character in uppercase.
    """
    inp = str(inp)
    return inp[:1].upper() + inp[1:] if inp else ""


def is_url(url: str) -> bool:
    """Checks if the given string is a valid URL using urlparse.

    Args:
        url (str): The string to check.

    Returns:
        bool: True if the string is a valid URL, False otherwise.
    """
    parsed = urlparse(str(url).strip())
    return all([parsed.scheme, parsed.netloc])


def titleize_name(name: str) -> str:
    """Converts a camelCase name to a TitleCase name.

    Args:
        name (str): The camelCase name.

    Returns:
        str: The TitleCase name.
    """
    return inflection.titleize(inflection.underscore(str(name)))
