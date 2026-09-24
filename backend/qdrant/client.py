"""Qdrant Cloud client factory + health ping."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from qdrant import config


@lru_cache(maxsize=1)
def get_client():
    """Lazy singleton. Raises if QDRANT_URL / QDRANT_API_KEY missing."""
    from qdrant_client import QdrantClient

    if not config.url():
        raise RuntimeError("QDRANT_URL is not set")
    if not config.api_key():
        raise RuntimeError("QDRANT_API_KEY is not set")

    return QdrantClient(
        url=config.url(),
        api_key=config.api_key(),
        timeout=config.timeout_sec(),
        check_compatibility=False,
    )


def reset_client() -> None:
    get_client.cache_clear()


def ping() -> dict[str, Any]:
    """Authenticated connectivity check (no secrets in the result)."""
    client = get_client()
    collections = client.get_collections()
    names = [c.name for c in (collections.collections or [])]
    return {
        "ok": True,
        "url_host": config.url_host(),
        "collections": names,
        "collection_count": len(names),
    }
