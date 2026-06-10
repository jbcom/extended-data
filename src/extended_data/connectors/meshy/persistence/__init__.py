"""Persistence layer for task manifests and resume capability.

Two storage backends are available:
1. JSON manifests (TaskRepository) - Simple file-based storage
2. SQLite vector store (VectorStore) - For idempotency + RAG embeddings

Usage:
    # Simple JSON manifests
    from extended_data.connectors.meshy.persistence import TaskRepository
    repo = TaskRepository("models/")

    # Vector-enabled SQLite for RAG
    from extended_data.connectors.meshy.persistence import VectorStore
    store = VectorStore("assets.db")
    store.record_generation(spec_hash, prompt, embedding=get_embedding(prompt))
    similar = store.search_similar(query_embedding)
"""

from __future__ import annotations

from extended_data.connectors.meshy.persistence.repository import TaskRepository
from extended_data.connectors.meshy.persistence.schemas import (
    ArtifactRecord,
    AssetManifest,
    ProjectManifest,
    TaskGraphEntry,
)
from extended_data.connectors.meshy.persistence.utils import canonicalize_spec, compute_spec_hash
from extended_data.connectors.meshy.persistence.vector_store import (
    GenerationRecord,
    SimilarityResult,
    VectorStore,
    get_embedding,
)


__all__ = [
    # JSON manifests
    "ArtifactRecord",
    "AssetManifest",
    "GenerationRecord",
    "ProjectManifest",
    "SimilarityResult",
    "TaskGraphEntry",
    "TaskRepository",
    # Vector store
    "VectorStore",
    "canonicalize_spec",
    "compute_spec_hash",
    "get_embedding",
]
