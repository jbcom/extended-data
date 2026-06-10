"""Tests for Tier 2 extended containers."""

from __future__ import annotations

from typing import Any

import extended_data

from extended_data.containers import (
    ExtendedDict,
    ExtendedList,
    ExtendedSet,
    ExtendedString,
    ExtendedTuple,
    extend_data,
    to_builtin,
)


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
    filtered = merged.filter(allowlist=["outer"])
    accepted, rejected = filtered
    all_values = value.all_values()

    assert isinstance(filtered, ExtendedTuple)
    assert isinstance(accepted, ExtendedDict)
    assert isinstance(rejected, ExtendedDict)
    assert isinstance(all_values, ExtendedList)
    assert merged["outer"] == {"inner": 1, "other": 2}
    assert value["outer"] == {"inner": 1}
    assert value.flatten() == {"outer.inner": 1, "items.0": 1, "items.1": 1, "items.2": 2, "empty": ""}
    assert value.deduplicate()["items"] == [1, 2]
    assert value.compact() == {"outer": {"inner": 1}, "items": [1, 1, 2]}
    assert accepted == {"outer": {"inner": 1, "other": 2}}
    assert "items" in rejected
    assert all_values == [1, 1, 1, 2, ""]
    assert isinstance(all_values[-1], ExtendedString)


def test_extended_dict_promotes_nested_values_on_mutation() -> None:
    """ExtendedDict keeps nested values in the Tier 2 surface."""
    value = ExtendedDict({"service": {"name": "api"}})

    value["owner"] = "platform"
    value.update({"ports": [8080, "9090"]})
    value.update([("metadata", {"tier": "prod"})], runtime={"python": "3.13"})
    value.update(other={"literal": "key"})
    defaulted = value.setdefault("labels", {"team": "data"})
    existing = value.setdefault("labels", {"team": "ignored"})
    merged = value | {"deployment": {"region": "us-east-1"}}
    right_merged = {"cluster": {"name": "primary"}} | value
    value |= {"settings": {"debug": "false"}}

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
    assert isinstance(defaulted, ExtendedDict)
    assert isinstance(defaulted["team"], ExtendedString)
    assert existing is defaulted
    assert value["labels"]["team"] == "data"
    assert isinstance(value["settings"], ExtendedDict)
    assert isinstance(value["settings"]["debug"], ExtendedString)
    assert isinstance(merged, ExtendedDict)
    assert isinstance(merged["deployment"], ExtendedDict)
    assert isinstance(merged["deployment"]["region"], ExtendedString)
    assert isinstance(right_merged, ExtendedDict)
    assert isinstance(right_merged["cluster"], ExtendedDict)
    assert isinstance(right_merged["cluster"]["name"], ExtendedString)
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


def test_extended_tuple_preserves_immutable_sequence_shape() -> None:
    """ExtendedTuple composes sequence primitives without becoming an ExtendedList."""
    value = ExtendedTuple((1, (2, [3]), "", 2))

    assert value.flatten() == (1, 2, 3, "", 2)
    assert value.compact() == (1, (2, [3]), 2)
    assert value.unique() == (1, (2, [3]), "", 2)
    assert value.filter(lambda item: isinstance(item, int)) == (1, 2)
    assert value.map(lambda item: item * 2 if isinstance(item, int) else item) == (2, (2, [3]), "", 4)


def test_extended_tuple_promotes_nested_values() -> None:
    """ExtendedTuple keeps tuple-shaped values in the Tier 2 surface."""
    value = ExtendedTuple(({"name": "api"}, ["jobs"]))

    assert isinstance(value[0], ExtendedDict)
    assert isinstance(value[0]["name"], ExtendedString)
    assert isinstance(value[1], ExtendedList)
    assert isinstance(value[1][0], ExtendedString)
    assert value.to_tuple() == ({"name": "api"}, ["jobs"])
    assert to_builtin(value) == ({"name": "api"}, ["jobs"])


def test_extended_tuple_preserves_surface_for_builtin_tuple_operations() -> None:
    """Inherited tuple operations should not leak plain tuple results."""
    value = ExtendedTuple(({"name": "api"}, ["jobs"]))
    prefix = ({"name": "gateway"},)
    suffix = ({"name": "worker"},)

    sliced = value[:1]
    added = value + suffix
    right_added = prefix + value
    repeated = value * 2
    right_repeated = 2 * value

    assert isinstance(sliced, ExtendedTuple)
    assert isinstance(added, ExtendedTuple)
    assert isinstance(right_added, ExtendedTuple)
    assert isinstance(repeated, ExtendedTuple)
    assert isinstance(right_repeated, ExtendedTuple)
    assert isinstance(sliced[0], ExtendedDict)
    assert isinstance(added[2], ExtendedDict)
    assert isinstance(added[2]["name"], ExtendedString)
    assert isinstance(right_added[0], ExtendedDict)
    assert isinstance(right_added[0]["name"], ExtendedString)
    assert isinstance(repeated[2], ExtendedDict)
    assert isinstance(right_repeated[2], ExtendedDict)


def test_extend_data_recursively_wraps_builtin_containers() -> None:
    """The container factory promotes plain values into the Tier 2 surface."""
    wrapped = extend_data(
        {
            "service": {"name": "api"},
            "ports": [8080, 8081],
            "tags": {"prod", "api"},
            "aliases": ("api", "gateway"),
        }
    )

    assert isinstance(wrapped, ExtendedDict)
    assert isinstance(wrapped["service"], ExtendedDict)
    assert isinstance(wrapped["service"]["name"], ExtendedString)
    assert isinstance(wrapped["ports"], ExtendedList)
    assert isinstance(wrapped["tags"], ExtendedSet)
    assert isinstance(wrapped["aliases"], ExtendedTuple)
    assert wrapped["service"]["name"].upper_first() == "Api"


def test_to_builtin_recursively_unwraps_extended_containers() -> None:
    """Extended containers can be lowered back to normal Python data."""
    wrapped = ExtendedDict(
        {
            "service": ExtendedDict({"name": ExtendedString("api")}),
            "ports": ExtendedList([8080, 8081]),
            "tags": ExtendedSet({"prod", "api"}),
            "aliases": ExtendedTuple(("api", "gateway")),
        }
    )

    plain = to_builtin(wrapped)

    assert isinstance(plain, dict)
    assert plain["service"] == {"name": "api"}
    assert plain["ports"] == [8080, 8081]
    assert plain["tags"] == {"prod", "api"}
    assert plain["aliases"] == ("api", "gateway")


def test_container_classes_are_root_exports() -> None:
    """Tier 2 containers are root-level convenience exports."""
    assert extended_data.ExtendedString is ExtendedString
    assert extended_data.ExtendedDict is ExtendedDict
    assert extended_data.ExtendedList is ExtendedList
    assert extended_data.ExtendedSet is ExtendedSet
    assert extended_data.ExtendedTuple is ExtendedTuple
    assert extended_data.extend_data is extend_data
    assert extended_data.to_builtin is to_builtin
