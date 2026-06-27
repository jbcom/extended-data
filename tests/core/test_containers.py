"""Tests for Tier 2 extended containers."""

from __future__ import annotations

import datetime
import json

from collections import UserDict, UserList, UserString
from collections.abc import MutableSet
from pathlib import Path
from typing import Any

import pytest

import extended_data

from extended_data.containers import (
    ExtendedData,
    ExtendedDict,
    ExtendedList,
    ExtendedSet,
    ExtendedString,
    ExtendedTuple,
    extend_data,
    to_builtin,
)


def test_tier2_containers_inherit_expected_python_bases() -> None:
    """Tier 2 classes should be real extended primitives, not detached facades."""
    assert issubclass(ExtendedString, UserString)
    assert issubclass(ExtendedDict, UserDict)
    assert issubclass(ExtendedList, UserList)
    assert issubclass(ExtendedTuple, tuple)
    assert issubclass(ExtendedSet, MutableSet)
    assert isinstance(ExtendedString("api"), UserString)
    assert isinstance(ExtendedDict({"service": "api"}), UserDict)
    assert isinstance(ExtendedList(["api"]), UserList)
    assert isinstance(ExtendedTuple(("api",)), tuple)
    assert isinstance(ExtendedSet({"api"}), MutableSet)


def test_extended_string_chains_primitive_transforms() -> None:
    """ExtendedString composes Tier 1 string primitives."""
    value = ExtendedString("API Response Value")
    partitioned = ExtendedString("api.gateway.worker").partition(".")
    right_partitioned = ExtendedString("api.gateway.worker").rpartition(".")
    split = ExtendedString("api,gateway,worker").split(",")
    right_split = ExtendedString("api,gateway,worker").rsplit(",", 1)
    lines = ExtendedString("api\ngateway").splitlines()
    joined = ExtendedString(",").join([ExtendedString("api"), "gateway"])
    formatted = ExtendedString("{service}.{component}").format(service="api", component=ExtendedString("worker"))
    formatted_map = ExtendedString("{service}.{component}").format_map(
        {"service": ExtendedString("api"), "component": "worker"}
    )
    decoded_json = ExtendedString('{"service": {"name": "api"}}').decode_json()
    decoded_yaml = ExtendedString("service:\n  name: api\n").decode_yaml()
    decoded_toml = ExtendedString('service = { name = "api" }\n').decode_toml()
    decoded_hcl = ExtendedString('locals { service = "api" }\n').decode_hcl2()
    encoded_base64 = ExtendedString('{"service": {"name": "api"}}').encode_base64(wrap_raw_data=False)
    decoded_base64 = encoded_base64.decode_base64(encoding="json")
    plain_decoded_json = ExtendedString('{"service": "api"}').decode_json(as_extended=False)

    assert value.to_snake_case().remove_suffix("_value") == "api_response"
    assert value.to_snake_case().remove_prefix("api_") == "response_value"
    assert ExtendedString("prefix_value").remove_prefix("prefix_") == "value"
    assert ExtendedString("value_suffix").remove_suffix("_suffix") == "value"
    assert value.to_kebab_case() == "api-response-value"
    assert ExtendedString("1").ordinalize() == "1st"
    assert ExtendedString("yes").to_bool() is True
    assert ExtendedString("42").to_int() == 42
    assert ExtendedString("3.14").to_float() == 3.14
    assert ExtendedString("/tmp/service.yaml").to_path() == Path("/tmp/service.yaml")
    assert ExtendedString("2026-06-10").to_date() == datetime.date(2026, 6, 10)
    assert ExtendedString("2026-06-10").reconstruct_special_type() == datetime.date(2026, 6, 10)
    assert ExtendedString("echo one\necho two").to_export_safe(export_to_yaml=True) == "echo one\necho two"
    assert json.loads(ExtendedString("api").wrap_for_export(allow_encoding="json")) == "api"
    reconstructed_json = ExtendedString('{"service": "api"}').reconstruct_special_type()
    assert isinstance(reconstructed_json, ExtendedDict)
    assert reconstructed_json["service"].upper_first() == "Api"
    assert ExtendedString("2026-06-10T12:30:00").to_datetime() == datetime.datetime(
        2026,
        6,
        10,
        12,
        30,
        0,
        tzinfo=datetime.UTC,
    )
    assert ExtendedString("12:30").to_time() == datetime.time(12, 30)
    assert ExtendedString("api-gateway").is_partial_match("gateway") is True
    assert ExtendedString("api").is_partial_match("gateway", check_prefix_only=True) is False
    assert ExtendedString("API").is_non_empty_match("api") is True
    assert ExtendedString("").is_non_empty_match("api") is False
    assert isinstance(partitioned, ExtendedTuple)
    assert isinstance(partitioned[0], ExtendedString)
    assert partitioned == ("api", ".", "gateway.worker")
    assert isinstance(right_partitioned, ExtendedTuple)
    assert right_partitioned == ("api.gateway", ".", "worker")
    assert isinstance(split, ExtendedList)
    assert all(isinstance(item, ExtendedString) for item in split)
    assert split == ["api", "gateway", "worker"]
    assert isinstance(right_split, ExtendedList)
    assert right_split == ["api,gateway", "worker"]
    assert isinstance(lines, ExtendedList)
    assert all(isinstance(item, ExtendedString) for item in lines)
    assert lines == ["api", "gateway"]
    assert isinstance(joined, ExtendedString)
    assert joined == "api,gateway"
    assert isinstance(formatted, ExtendedString)
    assert formatted == "api.worker"
    assert isinstance(formatted_map, ExtendedString)
    assert formatted_map == "api.worker"
    assert isinstance(decoded_json, ExtendedDict)
    assert decoded_json["service"]["name"].upper_first() == "Api"
    assert isinstance(decoded_yaml, ExtendedDict)
    assert decoded_yaml["service"]["name"].upper_first() == "Api"
    assert isinstance(decoded_toml, ExtendedDict)
    assert decoded_toml["service"]["name"].upper_first() == "Api"
    assert isinstance(decoded_hcl, ExtendedDict)
    assert isinstance(decoded_hcl["locals"], ExtendedList)
    assert decoded_hcl["locals"][0]["service"].upper_first() == "Api"
    assert isinstance(encoded_base64, ExtendedString)
    assert isinstance(decoded_base64, ExtendedDict)
    assert decoded_base64["service"]["name"].upper_first() == "Api"
    assert isinstance(plain_decoded_json, dict)
    assert plain_decoded_json == {"service": "api"}


def test_extended_dict_composes_mapping_primitives() -> None:
    """ExtendedDict composes Tier 1 mapping primitives."""
    value = ExtendedDict({"outer": {"inner": 1}, "items": [1, 1, 2], "empty": ""})
    typed = ExtendedDict({"service": "api", "retries": 2, "enabled": True, "ports": [80, 443]})
    reconstructed = ExtendedDict(
        {"enabled": "true", "retries": "5", "service": {"launched": "2026-06-10"}, "ports": ["80"]}
    ).reconstruct_special_types()
    export_safe = ExtendedDict(
        {"launched": datetime.date(2026, 6, 10), "path": Path("/tmp/service.yaml")}
    ).to_export_safe()
    wrapped_json = ExtendedDict({"service": "api", "retries": 2}).wrap_for_export(allow_encoding="json")

    merged = value.deep_merge({"outer": {"other": 2}})
    filtered = merged.filter(allowlist=["outer"])
    accepted, rejected = filtered
    all_values = value.all_values()
    split = typed.split_by_type(primitive_only=True)
    first_scalar = typed.first_non_empty_value("missing", "service")
    first_nested = value.first_non_empty_value("missing", "outer")
    first_entry = typed.first_non_empty_entry("missing", "service", "ports")
    entries = typed.non_empty_entries("missing", "service", "ports")

    assert isinstance(filtered, ExtendedTuple)
    assert isinstance(accepted, ExtendedDict)
    assert isinstance(rejected, ExtendedDict)
    assert isinstance(all_values, ExtendedList)
    assert isinstance(split, ExtendedDict)
    assert isinstance(split["str"], ExtendedDict)
    assert isinstance(split["list"], ExtendedDict)
    assert isinstance(first_scalar, ExtendedString)
    assert isinstance(first_nested, ExtendedDict)
    assert isinstance(first_entry, ExtendedDict)
    assert isinstance(entries, ExtendedList)
    assert all(isinstance(entry, ExtendedDict) for entry in entries)
    assert isinstance(reconstructed, ExtendedDict)
    assert isinstance(reconstructed["service"], ExtendedDict)
    assert isinstance(reconstructed["ports"], ExtendedList)
    assert export_safe == {"launched": "2026-06-10", "path": "/tmp/service.yaml"}
    assert json.loads(wrapped_json) == {"service": "api", "retries": 2}
    assert merged["outer"] == {"inner": 1, "other": 2}
    assert value["outer"] == {"inner": 1}
    assert value.flatten() == {"outer.inner": 1, "items.0": 1, "items.1": 1, "items.2": 2, "empty": ""}
    assert value.deduplicate()["items"] == [1, 2]
    assert value.compact() == {"outer": {"inner": 1}, "items": [1, 1, 2]}
    assert accepted == {"outer": {"inner": 1, "other": 2}}
    assert "items" in rejected
    assert all_values == [1, 1, 1, 2, ""]
    assert isinstance(all_values[-1], ExtendedString)
    assert split["str"] == {"service": "api"}
    assert split["int"] == {"retries": 2}
    assert split["bool"] == {"enabled": True}
    assert split["list"] == {"ports": [80, 443]}
    assert first_scalar.upper_first() == "Api"
    assert first_nested["inner"] == 1
    assert first_entry["service"].upper_first() == "Api"
    assert entries == [{"service": "api"}, {"ports": [80, 443]}]
    assert isinstance(entries[1]["ports"], ExtendedList)
    assert reconstructed["enabled"] is True
    assert reconstructed["retries"] == 5
    assert reconstructed["service"]["launched"] == datetime.date(2026, 6, 10)
    assert reconstructed["ports"] == [80]


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


def test_extended_dict_update_accepts_keys_getitem_mappings() -> None:
    """Mapping-like objects should route through __setitem__ promotion."""

    class KeyedMapping:
        def __init__(self) -> None:
            self._data = {"service": {"name": "api"}}

        def keys(self) -> list[str]:
            return list(self._data)

        def __getitem__(self, key: str) -> object:
            return self._data[key]

    value = ExtendedDict()

    value.update(KeyedMapping())

    assert isinstance(value["service"], ExtendedDict)
    assert isinstance(value["service"]["name"], ExtendedString)
    assert value["service"]["name"].upper_first() == "Api"


def test_extended_list_composes_sequence_primitives() -> None:
    """ExtendedList composes Tier 1 sequence primitives."""
    value = ExtendedList([1, [2, [3]], "", 2])
    typed = ExtendedList(["api", 2, True, ["nested"]])
    first_nested = ExtendedList([None, "", {"service": "api"}]).first_non_empty()
    mapped = ExtendedList(["service", "region", "ignored"]).zipmap(["api", "us-east-1"])
    reconstructed = ExtendedList(["true", "5", {"launched": "2026-06-10"}]).reconstruct_special_types()
    export_safe = ExtendedList([datetime.date(2026, 6, 10), Path("/tmp/service.yaml")]).to_export_safe()

    assert value.flatten() == [1, 2, 3, "", 2]
    assert value.compact() == [1, [2, [3]], 2]
    assert value.unique() == [1, [2, [3]], "", 2]
    assert isinstance(first_nested, ExtendedDict)
    assert first_nested["service"].upper_first() == "Api"
    assert isinstance(mapped, ExtendedDict)
    assert mapped == {"service": "api", "region": "us-east-1"}
    assert mapped["service"].upper_first() == "Api"
    assert isinstance(reconstructed, ExtendedList)
    assert isinstance(reconstructed[2], ExtendedDict)
    assert reconstructed == [True, 5, {"launched": datetime.date(2026, 6, 10)}]
    assert export_safe == ["2026-06-10", "/tmp/service.yaml"]
    assert value.filter(lambda item: isinstance(item, int)) == [1, 2]
    assert ExtendedList([1, 2]).map(lambda item: item * 2) == [2, 4]
    assert ExtendedList(["api", "worker", "db"]).filter_values(
        allowlist=["api", "worker"],
        denylist=["worker"],
    ) == ["api"]
    split = typed.split_by_type(primitive_only=True)
    assert isinstance(split, ExtendedDict)
    assert isinstance(split["str"], ExtendedList)
    assert isinstance(split["list"], ExtendedList)
    assert split["str"] == ["api"]
    assert split["int"] == [2]
    assert split["bool"] == [True]
    assert split["list"] == [["nested"]]


def test_extended_list_promotes_nested_values_on_mutation() -> None:
    """ExtendedList keeps nested values in the Tier 2 surface."""
    value: ExtendedList[Any] = ExtendedList([{"name": "api"}])
    in_place: ExtendedList[Any] = ExtendedList([{"name": "api"}])

    value.append("worker")
    value.extend([{"name": "scheduler"}])
    value.insert(0, ["frontdoor"])
    value[1] = {"name": "gateway"}
    value[2:3] = ["jobs"]
    in_place += [{"name": "worker"}, ["jobs"]]
    in_place *= 2

    assert isinstance(value[0], ExtendedList)
    assert isinstance(value[0][0], ExtendedString)
    assert isinstance(value[1], ExtendedDict)
    assert isinstance(value[1]["name"], ExtendedString)
    assert isinstance(value[2], ExtendedString)
    assert isinstance(value[3], ExtendedDict)
    assert value[1]["name"].upper_first() == "Gateway"
    assert isinstance(in_place[1], ExtendedDict)
    assert isinstance(in_place[1]["name"], ExtendedString)
    assert isinstance(in_place[2], ExtendedList)
    assert isinstance(in_place[2][0], ExtendedString)
    assert isinstance(in_place[4], ExtendedDict)
    assert isinstance(in_place[5], ExtendedList)


def test_extended_set_composes_set_operations() -> None:
    """ExtendedSet provides chainable set operations."""
    value = ExtendedSet({1, 2, 3, None})
    reconstructed = ExtendedSet({"true", "2026-06-10"}).reconstruct_special_types()
    export_safe = ExtendedSet({datetime.date(2026, 6, 10)}).to_export_safe()

    compact_repr = repr(value.compact())
    assert compact_repr.startswith("ExtendedSet(")
    assert "object at" not in compact_repr
    assert isinstance(reconstructed, ExtendedSet)
    assert reconstructed.to_set() == {True, datetime.date(2026, 6, 10)}
    assert export_safe == ["2026-06-10"]
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


def test_extended_set_named_mutators_preserve_extended_values() -> None:
    """Named set mutation methods keep values in the Tier 2 surface."""
    value = ExtendedSet({"api"})

    value.update(["worker"], {"scheduler"})
    symmetric = value.symmetric_difference({"worker", "batch"})
    value.intersection_update({"api", "scheduler", "batch"})
    value.difference_update({"scheduler"})
    value.symmetric_difference_update({"api", "batch"})

    assert isinstance(symmetric, ExtendedSet)
    assert symmetric.to_set() == {"api", "scheduler", "batch"}
    assert all(isinstance(item, ExtendedString) for item in symmetric)
    assert value.to_set() == {"batch"}
    assert all(isinstance(item, ExtendedString) for item in value)


def test_extended_tuple_preserves_immutable_sequence_shape() -> None:
    """ExtendedTuple composes sequence primitives without becoming an ExtendedList."""
    value = ExtendedTuple((1, (2, [3]), "", 2))
    typed = ExtendedTuple(("api", 2, True, ["nested"]))
    first_nested = ExtendedTuple((None, "", {"service": "api"})).first_non_empty()
    mapped = ExtendedTuple(("service", "region", "ignored")).zipmap(("api", "us-east-1"))
    reconstructed = ExtendedTuple(("true", "5", {"launched": "2026-06-10"})).reconstruct_special_types()
    export_safe = ExtendedTuple((datetime.date(2026, 6, 10), Path("/tmp/service.yaml"))).to_export_safe()
    split = typed.split_by_type(primitive_only=True)

    assert value.flatten() == (1, 2, 3, "", 2)
    assert value.compact() == (1, (2, [3]), 2)
    assert value.unique() == (1, (2, [3]), "", 2)
    assert isinstance(first_nested, ExtendedDict)
    assert first_nested["service"].upper_first() == "Api"
    assert isinstance(mapped, ExtendedDict)
    assert mapped == {"service": "api", "region": "us-east-1"}
    assert mapped["service"].upper_first() == "Api"
    assert isinstance(reconstructed, ExtendedTuple)
    assert isinstance(reconstructed[2], ExtendedDict)
    assert reconstructed == (True, 5, {"launched": datetime.date(2026, 6, 10)})
    assert export_safe == ["2026-06-10", "/tmp/service.yaml"]
    assert value.filter(lambda item: isinstance(item, int)) == (1, 2)
    assert value.map(lambda item: item * 2 if isinstance(item, int) else item) == (2, (2, [3]), "", 4)
    assert isinstance(split, ExtendedDict)
    assert isinstance(split["str"], ExtendedTuple)
    assert isinstance(split["list"], ExtendedTuple)
    assert split["str"] == ("api",)
    assert split["int"] == (2,)
    assert split["bool"] == (True,)
    assert split["list"] == (["nested"],)


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


def test_extended_data_is_generic_container_for_unknown_shapes(tmp_path: Path) -> None:
    """ExtendedData should hold and operate on any promoted data shape."""
    vendor = ExtendedData({"vendor": "google", "payload": {"names": ["alpha"]}})
    sequence = ExtendedData([{"name": "api"}]).append({"name": "worker"})
    scalar = ExtendedData(42)
    decoded = ExtendedData.decode('{"service": {"name": "api"}}', suffix="json")
    file_path = tmp_path / "config.yaml"
    file_path.write_text("service:\n  name: api\n", encoding="utf-8")
    loaded = ExtendedData.read(file_path)
    synced = loaded.sync_to_file(tmp_path / "out.json", encoding="json", source="test")

    vendor["enabled"] = "true"
    merged = vendor.merge({"payload": {"region": "us-east-1"}})
    mapped = vendor.map_builtin(lambda data: {**data, "vendor": data["vendor"].upper()})

    assert vendor.shape == "mapping"
    assert vendor.is_mapping is True
    assert vendor.data_type == "ExtendedDict"
    assert isinstance(vendor.value, ExtendedDict)
    assert vendor.get("vendor").upper_first() == "Google"
    assert vendor["payload"]["names"][0].upper_first() == "Alpha"
    assert isinstance(vendor["enabled"], ExtendedString)
    assert "vendor" in vendor
    assert merged.as_builtin()["payload"]["region"] == "us-east-1"
    assert mapped.as_builtin()["vendor"] == "GOOGLE"
    assert sequence.shape == "list"
    assert sequence.is_sequence is True
    assert isinstance(sequence[1], ExtendedDict)
    assert sequence[1]["name"].upper_first() == "Worker"
    assert scalar.shape == "scalar"
    assert scalar.is_scalar is True
    assert len(scalar) == 1
    assert list(scalar) == [42]
    assert decoded.shape == "mapping"
    assert decoded["service"]["name"].upper_first() == "Api"
    assert loaded.shape == "mapping"
    assert loaded["service"]["name"].upper_first() == "Api"
    assert synced.changed is True
    assert json.loads((tmp_path / "out.json").read_text(encoding="utf-8")) == {"service": {"name": "api"}}


def test_extended_data_detects_string_set_none_and_object_shapes() -> None:
    """ExtendedData exposes broad shape predicates for non-mapping data too."""

    class VendorRecord:
        pass

    text = ExtendedData("HTTP Response Value")
    tags = ExtendedData({"prod", "api"}).add("sync")
    empty = ExtendedData()
    record = ExtendedData(VendorRecord())

    assert text.shape == "string"
    assert text.is_string is True
    assert text.to_snake_case() == "http_response_value"
    assert tags.shape == "set"
    assert tags.is_set is True
    assert "sync" in tags
    assert empty.shape == "none"
    assert empty.is_none is True
    assert record.shape == "object"
    assert record.copy().shape == "object"


def test_extended_data_getattr_fails_cleanly_before_initialization() -> None:
    """Uninitialized wrappers should not recurse when attributes are missing."""
    uninitialized = object.__new__(ExtendedData)

    with pytest.raises(AttributeError, match="missing"):
        _ = uninitialized.missing


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
            ExtendedString("metadata"): ExtendedDict({"owner": ExtendedString("platform")}),
            "ports": ExtendedList([8080, 8081]),
            "tags": ExtendedSet({"prod", "api"}),
            "aliases": ExtendedTuple(("api", "gateway")),
        }
    )

    plain = to_builtin(wrapped)

    assert isinstance(plain, dict)
    assert plain["service"] == {"name": "api"}
    metadata_key = next(key for key in plain if key == "metadata")
    assert type(metadata_key) is str
    assert plain["metadata"] == {"owner": "platform"}
    assert plain["ports"] == [8080, 8081]
    assert plain["tags"] == {"prod", "api"}
    assert plain["aliases"] == ("api", "gateway")


def test_container_classes_are_root_exports() -> None:
    """Tier 2 containers are root-level convenience exports."""
    assert extended_data.ExtendedData is ExtendedData
    assert extended_data.ExtendedString is ExtendedString
    assert extended_data.ExtendedDict is ExtendedDict
    assert extended_data.ExtendedList is ExtendedList
    assert extended_data.ExtendedSet is ExtendedSet
    assert extended_data.ExtendedTuple is ExtendedTuple
    assert extended_data.extend_data is extend_data
    assert extended_data.to_builtin is to_builtin
