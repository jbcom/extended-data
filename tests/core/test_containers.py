"""Tests for Tier 2 extended containers."""

from __future__ import annotations

from typing import Any

import extended_data

from extended_data.containers import ExtendedDict, ExtendedList, ExtendedSet, ExtendedString, extend_data, to_builtin


def test_extended_string_chains_primitive_transforms() -> None:
    """ExtendedString composes Tier 1 string primitives."""
    value = ExtendedString("API Response Value")

    assert value.to_snake_case().remove_suffix("_value") == "api_response"
    assert value.to_kebab_case() == "api-response-value"
    assert ExtendedString("1").ordinalize() == "1st"
    assert ExtendedString("yes").to_bool() is True


def test_extended_dict_composes_mapping_primitives() -> None:
    """ExtendedDict composes Tier 1 mapping primitives."""
    value = ExtendedDict({"outer": {"inner": 1}, "items": [1, 1, 2], "empty": ""})

    merged = value.deep_merge({"outer": {"other": 2}})
    accepted, rejected = merged.filter(allowlist=["outer"])

    assert merged["outer"] == {"inner": 1, "other": 2}
    assert value["outer"] == {"inner": 1}
    assert value.flatten() == {"outer.inner": 1, "items.0": 1, "items.1": 1, "items.2": 2, "empty": ""}
    assert value.deduplicate()["items"] == [1, 2]
    assert value.compact() == {"outer": {"inner": 1}, "items": [1, 1, 2]}
    assert accepted == {"outer": {"inner": 1, "other": 2}}
    assert "items" in rejected


def test_extended_dict_promotes_nested_values_on_mutation() -> None:
    """ExtendedDict keeps nested values in the Tier 2 surface."""
    value = ExtendedDict({"service": {"name": "api"}})

    value["owner"] = "platform"
    value.update({"ports": [8080, "9090"]})
    value.update([("metadata", {"tier": "prod"})], runtime={"python": "3.13"})
    value.update(other={"literal": "key"})

    assert isinstance(value["service"], ExtendedDict)
    assert isinstance(value["service"]["name"], ExtendedString)
    assert isinstance(value["owner"], ExtendedString)
    assert isinstance(value["ports"], ExtendedList)
    assert isinstance(value["ports"][1], ExtendedString)
    assert isinstance(value["metadata"], ExtendedDict)
    assert isinstance(value["metadata"]["tier"], ExtendedString)
    assert isinstance(value["runtime"], ExtendedDict)
    assert isinstance(value["runtime"]["python"], ExtendedString)
    assert isinstance(value["other"], ExtendedDict)
    assert isinstance(value["other"]["literal"], ExtendedString)
    assert value["service"]["name"].upper_first() == "Api"


def test_extended_list_composes_sequence_primitives() -> None:
    """ExtendedList composes Tier 1 sequence primitives."""
    value = ExtendedList([1, [2, [3]], "", 2])

    assert value.flatten() == [1, 2, 3, "", 2]
    assert value.compact() == [1, [2, [3]], 2]
    assert value.unique() == [1, [2, [3]], "", 2]
    assert value.filter(lambda item: isinstance(item, int)) == [1, 2]
    assert ExtendedList([1, 2]).map(lambda item: item * 2) == [2, 4]


def test_extended_list_promotes_nested_values_on_mutation() -> None:
    """ExtendedList keeps nested values in the Tier 2 surface."""
    value: ExtendedList[Any] = ExtendedList([{"name": "api"}])

    value.append("worker")
    value.extend([{"name": "scheduler"}])
    value.insert(0, ["frontdoor"])
    value[1] = {"name": "gateway"}
    value[2:3] = ["jobs"]

    assert isinstance(value[0], ExtendedList)
    assert isinstance(value[0][0], ExtendedString)
    assert isinstance(value[1], ExtendedDict)
    assert isinstance(value[1]["name"], ExtendedString)
    assert isinstance(value[2], ExtendedString)
    assert isinstance(value[3], ExtendedDict)
    assert value[1]["name"].upper_first() == "Gateway"


def test_extended_set_composes_set_operations() -> None:
    """ExtendedSet provides chainable set operations."""
    value = ExtendedSet({1, 2, 3, None})

    assert value.compact().to_set() == {1, 2, 3}
    assert value.union({4}).to_set() == {1, 2, 3, 4, None}
    assert value.intersection({2, 3, 5}).to_set() == {2, 3}
    assert value.difference({1, None}).to_set() == {2, 3}


def test_extended_set_promotes_string_values() -> None:
    """ExtendedSet keeps hashable nested values in the Tier 2 surface."""
    value = ExtendedSet({"api"})

    value.add("worker")

    assert all(isinstance(item, ExtendedString) for item in value)
    assert value.to_set() == {"api", "worker"}
    assert to_builtin(value) == {"api", "worker"}


def test_extend_data_recursively_wraps_builtin_containers() -> None:
    """The container factory promotes plain values into the Tier 2 surface."""
    wrapped = extend_data(
        {
            "service": {"name": "api"},
            "ports": [8080, 8081],
            "tags": {"prod", "api"},
        }
    )

    assert isinstance(wrapped, ExtendedDict)
    assert isinstance(wrapped["service"], ExtendedDict)
    assert isinstance(wrapped["service"]["name"], ExtendedString)
    assert isinstance(wrapped["ports"], ExtendedList)
    assert isinstance(wrapped["tags"], ExtendedSet)
    assert wrapped["service"]["name"].upper_first() == "Api"


def test_to_builtin_recursively_unwraps_extended_containers() -> None:
    """Extended containers can be lowered back to normal Python data."""
    wrapped = ExtendedDict(
        {
            "service": ExtendedDict({"name": ExtendedString("api")}),
            "ports": ExtendedList([8080, 8081]),
            "tags": ExtendedSet({"prod", "api"}),
        }
    )

    plain = to_builtin(wrapped)

    assert isinstance(plain, dict)
    assert plain["service"] == {"name": "api"}
    assert plain["ports"] == [8080, 8081]
    assert plain["tags"] == {"prod", "api"}


def test_container_classes_are_root_exports() -> None:
    """Tier 2 containers are root-level convenience exports."""
    assert extended_data.ExtendedString is ExtendedString
    assert extended_data.ExtendedDict is ExtendedDict
    assert extended_data.ExtendedList is ExtendedList
    assert extended_data.ExtendedSet is ExtendedSet
    assert extended_data.extend_data is extend_data
    assert extended_data.to_builtin is to_builtin
