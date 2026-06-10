"""Tests for Meshy vector store persistence helpers."""

from __future__ import annotations

from extended_data.connectors.meshy.persistence import vector_store as vector_store_module
from extended_data.connectors.meshy.persistence.vector_store import VectorStore
from extended_data.containers import ExtendedDict, ExtendedList, ExtendedString


def test_record_generation_returns_extended_payload(temp_dir) -> None:
    """Recording a generation should expose an extended mapping payload."""
    with VectorStore(temp_dir / "assets.db") as store:
        result = store.record_generation(
            spec_hash="hash-abc",
            prompt="cute otter character",
            project="project1",
            task_id="task-123",
            metadata={"source": "test"},
        )

    assert isinstance(result, ExtendedDict)
    assert result["spec_hash"] == "hash-abc"
    assert result["prompt"] == "cute otter character"
    assert isinstance(result["prompt"], ExtendedString)
    assert isinstance(result["metadata"], ExtendedDict)
    assert result["metadata"]["source"] == "test"
    assert isinstance(result["created_at"], ExtendedString)


def test_record_generation_is_idempotent_with_extended_payload(temp_dir) -> None:
    """Duplicate spec hashes should return the existing extended payload."""
    with VectorStore(temp_dir / "assets.db") as store:
        first = store.record_generation(
            spec_hash="hash-abc",
            prompt="first prompt",
            project="project1",
        )
        second = store.record_generation(
            spec_hash="hash-abc",
            prompt="second prompt",
            project="project1",
        )

    assert isinstance(second, ExtendedDict)
    assert second["id"] == first["id"]
    assert second["prompt"] == "first prompt"


def test_get_record_methods_return_extended_payloads(temp_dir) -> None:
    """Spec hash and task ID lookups should return extended mapping payloads."""
    with VectorStore(temp_dir / "assets.db") as store:
        store.record_generation(
            spec_hash="hash-abc",
            prompt="cute otter character",
            project="project1",
            task_id="task-123",
        )

        by_hash = store.get_by_spec_hash("hash-abc")
        by_task = store.get_by_task_id("task-123")

    assert isinstance(by_hash, ExtendedDict)
    assert by_hash["spec_hash"] == "hash-abc"
    assert isinstance(by_task, ExtendedDict)
    assert by_task["task_id"] == "task-123"


def test_search_text_and_list_pending_return_extended_payloads(temp_dir) -> None:
    """Search and pending queries should return extended lists of mappings."""
    with VectorStore(temp_dir / "assets.db") as store:
        store.record_generation(
            spec_hash="hash-otter",
            prompt="cute otter character",
            project="project1",
        )
        store.record_generation(
            spec_hash="hash-badger",
            prompt="armored badger character",
            project="project2",
        )
        store.update_status("hash-badger", "SUCCEEDED")

        search_results = store.search_text("otter")
        pending_results = store.list_pending(project="project1")

    assert isinstance(search_results, ExtendedList)
    assert len(search_results) == 1
    assert isinstance(search_results[0], ExtendedDict)
    assert search_results[0]["spec_hash"] == "hash-otter"

    assert isinstance(pending_results, ExtendedList)
    assert len(pending_results) == 1
    assert isinstance(pending_results[0]["prompt"], ExtendedString)
    assert pending_results[0]["project"] == "project1"


def test_search_similar_without_vector_extension_returns_extended_list(temp_dir, monkeypatch) -> None:
    """The no-vector fallback should still expose an extended list."""
    monkeypatch.setattr(vector_store_module, "_HAS_VECTOR", False)

    with VectorStore(temp_dir / "assets.db") as store:
        result = store.search_similar([0.0] * store.embedding_dim)

    assert isinstance(result, ExtendedList)
    assert result == []
