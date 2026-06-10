"""Integration tests for the ecosystem foundation."""

from __future__ import annotations

import tempfile

from pathlib import Path

import extended_data as edt


def test_integration_workflow_serialization_transformation_export():
    """**Feature: ecosystem-foundation, Requirement 10.1: Serialization + Transformation + Export Workflow**"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "test.yaml"

        # 1. Setup: Create a YAML file with some raw data
        raw_data = {
            "project_name": "My Great Project",
            "settings": {
                "enable_feature": "true",
                "max_retries": "5",
                "timeout": "30.5",
            },
            "items": ["item_one", "item_two"],
        }
        edt.write_file(tmp_path, raw_data)

        # 2. Read and decode through the Tier 3 file boundary
        loaded_data = edt.read_data_file(tmp_path)
        assert loaded_data == raw_data
        assert isinstance(loaded_data, edt.ExtendedDict)

        # 3. Transform: Convert types and transform strings
        transformed = {
            "name": loaded_data["project_name"].to_pascal_case(),
            "config": loaded_data["settings"].reconstruct_special_types(),
            "item_list": [item.humanize() for item in loaded_data["items"]],
        }

        assert transformed["name"] == "MyGreatProject"
        assert isinstance(transformed["config"], edt.ExtendedDict)
        assert transformed["config"]["enable_feature"] is True
        assert transformed["config"]["max_retries"] == 5
        assert transformed["item_list"] == ["Item one", "Item two"]

        # 4. Export: Make safe for export (e.g. GitHub Actions)
        export_safe = edt.make_raw_data_export_safe(transformed)
        assert isinstance(export_safe, dict)
        # Verify it's still equivalent
        assert export_safe["name"] == "MyGreatProject"


def test_integration_workflow_git_file_operations():
    """**Feature: ecosystem-foundation, Requirement 10.2: Git + File Operations Workflow**"""
    # Use the current repository for testing
    repo = edt.get_parent_repository(".")
    assert repo is not None

    repo_name = edt.get_repository_name(repo)
    assert repo_name in (None, "extended-data")

    # Resolve a local path relative to root
    resolved = edt.resolve_local_path("pyproject.toml")
    assert resolved.exists()
    assert resolved.name == "pyproject.toml"

    # Read the file
    content = edt.read_file(resolved)
    assert "extended-data" in content


def test_integration_workflow_data_transformation_pipeline():
    """**Feature: ecosystem-foundation, Requirement 10.3: Data Transformation Pipeline**"""
    dict1 = {"a": {"b": 1}, "c": 3}
    dict2 = {"a": {"d": 4}, "e": 5}

    # 1. Merge maps
    merged = edt.deep_merge(dict1, dict2)
    assert merged["a"] == {"b": 1, "d": 4}

    # 2. Flatten map
    flattened = edt.flatten_map(merged)
    assert flattened["a.b"] == 1
    assert flattened["a.d"] == 4

    # 3. Transform keys
    unhumped = edt.unhump_map(merged)
    assert "a" in unhumped
