"""Extended sequence containers built on Tier 1 primitives."""

from __future__ import annotations

from collections import UserList
from collections.abc import Callable, Iterable, Iterator, MutableSet
from operator import index as operator_index
from typing import Any, SupportsIndex, TypeVar, cast, overload

from extended_data.primitives.sequences import flatten_list
from extended_data.primitives.state import is_nothing
from extended_data.primitives.types import make_hashable


T = TypeVar("T")
U = TypeVar("U")


class ExtendedList(UserList[T]):
    """List wrapper with chainable primitive operations."""

    def __init__(self, initlist: Iterable[T] | None = None) -> None:
        """Initialize the extended list."""
        super().__init__()
        self.extend(initlist or [])

    @staticmethod
    def _wrap_item(item: T) -> T:
        """Promote nested built-in containers to extended containers."""
        from extended_data.containers.factory import extend_data

        return cast(T, extend_data(item))

    @overload
    def __setitem__(self, i: SupportsIndex, item: T) -> None: ...

    @overload
    def __setitem__(self, i: slice, item: Iterable[T]) -> None: ...

    def __setitem__(self, i: SupportsIndex | slice, item: T | Iterable[T]) -> None:
        """Set values while preserving extended nested containers."""
        if isinstance(i, slice):
            self.data[i] = [self._wrap_item(value) for value in cast(Iterable[T], item)]
            return
        self.data[i] = self._wrap_item(cast(T, item))

    def append(self, item: T) -> None:
        """Append a value while preserving extended nested containers."""
        self.data.append(self._wrap_item(item))

    def extend(self, other: Iterable[T]) -> None:
        """Extend values while preserving extended nested containers."""
        self.data.extend(self._wrap_item(item) for item in other)

    def __iadd__(self, other: Iterable[T]) -> ExtendedList[T]:
        """Extend in place while preserving extended nested containers."""
        self.extend(other)
        return self

    def __imul__(self, count: SupportsIndex) -> ExtendedList[T]:
        """Repeat in place while preserving extended nested containers."""
        self.data *= operator_index(count)
        self.data[:] = [self._wrap_item(item) for item in self.data]
        return self

    def insert(self, i: int, item: T) -> None:
        """Insert a value while preserving extended nested containers."""
        self.data.insert(i, self._wrap_item(item))

    def flatten(self) -> ExtendedList[Any]:
        """Return a recursively flattened copy."""
        from extended_data.containers.factory import extend_data, to_builtin

        return extend_data(flatten_list(to_builtin(self.data)))

    def compact(self) -> ExtendedList[T]:
        """Return a copy without values considered empty."""
        return ExtendedList(item for item in self.data if not is_nothing(item))

    def map(self, func: Callable[[T], U]) -> ExtendedList[U]:
        """Return a copy with a callable applied to each item."""
        return ExtendedList(func(item) for item in self.data)

    def filter(self, predicate: Callable[[T], bool]) -> ExtendedList[T]:
        """Return a copy containing items accepted by a predicate."""
        return ExtendedList(item for item in self.data if predicate(item))

    def unique(self) -> ExtendedList[T]:
        """Return a copy with duplicate values removed while preserving order."""
        seen: set[Any] = set()
        values: list[T] = []
        for item in self.data:
            marker = make_hashable(item)
            if marker in seen:
                continue
            seen.add(marker)
            values.append(item)
        return ExtendedList(values)


class ExtendedTuple(tuple[T, ...]):
    """Tuple wrapper with immutable chainable sequence operations."""

    __slots__ = ()

    def __new__(cls, values: Iterable[T] | None = None) -> ExtendedTuple[T]:
        """Initialize the extended tuple."""
        items = () if values is None else values
        return super().__new__(cls, (cls._wrap_item(item) for item in items))

    @staticmethod
    def _wrap_item(item: T) -> T:
        """Promote nested built-in containers to extended containers."""
        from extended_data.containers.factory import extend_data

        return cast(T, extend_data(item))

    @overload
    def __getitem__(self, index: SupportsIndex) -> T: ...

    @overload
    def __getitem__(self, index: slice) -> ExtendedTuple[T]: ...

    def __getitem__(self, index: SupportsIndex | slice) -> T | ExtendedTuple[T]:
        """Return sliced values as ExtendedTuple instances."""
        value = super().__getitem__(index)
        if isinstance(index, slice):
            return ExtendedTuple(cast(tuple[T, ...], value))
        return cast(T, value)

    @overload
    def __add__(self, other: tuple[T, ...]) -> ExtendedTuple[T]: ...

    @overload
    def __add__(self, other: tuple[U, ...]) -> ExtendedTuple[T | U]: ...

    def __add__(self, other: tuple[Any, ...]) -> ExtendedTuple[Any]:
        """Concatenate tuples while preserving the ExtendedTuple surface."""
        return ExtendedTuple((*tuple(self), *other))

    def __radd__(self, other: tuple[Any, ...]) -> ExtendedTuple[Any]:
        """Concatenate tuples while preserving the ExtendedTuple surface."""
        return ExtendedTuple((*other, *tuple(self)))

    def __mul__(self, count: SupportsIndex) -> ExtendedTuple[T]:
        """Repeat tuple values while preserving the ExtendedTuple surface."""
        return ExtendedTuple(tuple(self) * operator_index(count))

    def __rmul__(self, count: SupportsIndex) -> ExtendedTuple[T]:
        """Repeat tuple values while preserving the ExtendedTuple surface."""
        return self * count

    def flatten(self) -> ExtendedTuple[Any]:
        """Return a recursively flattened tuple copy."""
        from extended_data.containers.factory import to_builtin

        def _flatten(items: Iterable[Any]) -> list[Any]:
            flattened: list[Any] = []
            for item in items:
                plain_item = to_builtin(item)
                if isinstance(plain_item, list | tuple):
                    flattened.extend(_flatten(plain_item))
                else:
                    flattened.append(plain_item)
            return flattened

        return ExtendedTuple(_flatten(self))

    def compact(self) -> ExtendedTuple[T]:
        """Return a copy without values considered empty."""
        return ExtendedTuple(item for item in self if not is_nothing(item))

    def map(self, func: Callable[[T], U]) -> ExtendedTuple[U]:
        """Return a copy with a callable applied to each item."""
        return ExtendedTuple(func(item) for item in self)

    def filter(self, predicate: Callable[[T], bool]) -> ExtendedTuple[T]:
        """Return a copy containing items accepted by a predicate."""
        return ExtendedTuple(item for item in self if predicate(item))

    def unique(self) -> ExtendedTuple[T]:
        """Return a copy with duplicate values removed while preserving order."""
        seen: set[Any] = set()
        values: list[T] = []
        for item in self:
            marker = make_hashable(item)
            if marker in seen:
                continue
            seen.add(marker)
            values.append(item)
        return ExtendedTuple(values)

    def to_tuple(self) -> tuple[T, ...]:
        """Return a plain tuple copy."""
        return tuple(self)


class ExtendedSet(MutableSet[T]):
    """Set wrapper with explicit chainable operations."""

    def __init__(self, values: Iterable[T] | None = None) -> None:
        """Initialize the extended set."""
        self._data: set[T] = set()
        for value in values or []:
            self.add(value)

    @staticmethod
    def _wrap_item(item: T) -> T:
        """Promote nested built-in containers to extended containers."""
        from extended_data.containers.factory import extend_data

        return cast(T, extend_data(item))

    def __contains__(self, value: object) -> bool:
        """Return whether the set contains a value."""
        return value in self._data

    def __iter__(self) -> Iterator[T]:
        """Iterate over set values."""
        return iter(self._data)

    def __len__(self) -> int:
        """Return the number of set values."""
        return len(self._data)

    def add(self, value: T) -> None:
        """Add a value to the set."""
        self._data.add(self._wrap_item(value))

    def discard(self, value: T) -> None:
        """Remove a value from the set if present."""
        self._data.discard(value)

    def copy(self) -> ExtendedSet[T]:
        """Return a shallow copy."""
        return ExtendedSet(self._data)

    def compact(self) -> ExtendedSet[T]:
        """Return a copy without values considered empty."""
        return ExtendedSet(item for item in self._data if not is_nothing(item))

    def union(self, *others: Iterable[T]) -> ExtendedSet[T]:
        """Return a union with other iterables."""
        result = set(self._data)
        for other in others:
            result.update(other)
        return ExtendedSet(result)

    def intersection(self, *others: Iterable[T]) -> ExtendedSet[T]:
        """Return an intersection with other iterables."""
        result = set(self._data)
        for other in others:
            result.intersection_update(other)
        return ExtendedSet(result)

    def difference(self, *others: Iterable[T]) -> ExtendedSet[T]:
        """Return a difference against other iterables."""
        result = set(self._data)
        for other in others:
            result.difference_update(other)
        return ExtendedSet(result)

    def to_set(self) -> set[T]:
        """Return a plain set copy."""
        return set(self._data)
