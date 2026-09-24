"""Collection create / ensure helpers (used before upload)."""

from __future__ import annotations

from qdrant import config
from qdrant.client import get_client


def ensure_collection(
    name: str,
    *,
    vector_size: int | None = None,
    recreate: bool = False,
) -> bool:
    """
    Create a dense-only cosine collection if missing (legacy upload).

    Returns True if created (or recreated), False if it already existed.
    """
    from qdrant_client.models import Distance, VectorParams

    client = get_client()
    size = vector_size or config.VECTOR_SIZE
    exists = client.collection_exists(name)

    if exists and not recreate:
        return False

    if exists and recreate:
        client.delete_collection(name)

    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=size, distance=Distance.COSINE),
    )
    return True


def ensure_hybrid_collection(
    name: str,
    *,
    vector_size: int | None = None,
    recreate: bool = False,
) -> bool:
    """
    Create dense + sparse (BM25) named-vector collection.

    Returns True if created (or recreated), False if it already existed.
    """
    from qdrant_client.models import (
        Distance,
        Modifier,
        SparseVectorParams,
        VectorParams,
    )

    client = get_client()
    size = vector_size or config.VECTOR_SIZE
    exists = client.collection_exists(name)

    if exists and not recreate:
        return False

    if exists and recreate:
        client.delete_collection(name)

    client.create_collection(
        collection_name=name,
        vectors_config={
            config.DENSE_VECTOR: VectorParams(size=size, distance=Distance.COSINE),
        },
        sparse_vectors_config={
            config.SPARSE_VECTOR: SparseVectorParams(modifier=Modifier.IDF),
        },
    )
    return True


def ensure_default_collections(*, recreate: bool = False) -> dict[str, bool]:
    """Ensure knowledge + assessment hybrid collections exist."""
    return {
        config.KNOWLEDGE_COLLECTION: ensure_hybrid_collection(
            config.KNOWLEDGE_COLLECTION, recreate=recreate
        ),
        config.ASSESSMENT_COLLECTION: ensure_hybrid_collection(
            config.ASSESSMENT_COLLECTION, recreate=recreate
        ),
    }


def collection_info(name: str) -> dict:
    """Point count + basic info for one collection."""
    client = get_client()
    if not client.collection_exists(name):
        return {"name": name, "exists": False, "points_count": 0}

    info = client.get_collection(name)
    return {
        "name": name,
        "exists": True,
        "points_count": int(info.points_count or 0),
        "status": str(info.status),
    }
