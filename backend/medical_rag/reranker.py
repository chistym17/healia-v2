"""
Thin client for the local TEI BGE reranker (:8081).

POST /rerank with query + candidate texts; map scores back by index.
"""

from __future__ import annotations

import os
from typing import Any

import requests
from dotenv import load_dotenv

DEFAULT_RERANK_URL = "http://localhost:8081/rerank"

# Env: RERANK_ENABLED=true|false (default true). When false, hybrid retrieval is used.
_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off"}


def is_rerank_enabled() -> bool:
    """Whether the BGE cross-encoder reranker should be called."""
    load_dotenv()
    raw = os.getenv("RERANK_ENABLED")
    if raw is None or not str(raw).strip():
        return True
    value = str(raw).strip().lower()
    if value in _FALSY:
        return False
    if value in _TRUTHY:
        return True
    return True


def resolve_rerank_url(cfg: dict | None = None) -> str:
    load_dotenv()
    if cfg:
        rerank = cfg.get("reranker", {})
        env_key = rerank.get("endpoint_env", "RERANK_SERVER")
        return os.getenv(env_key) or rerank.get("default_endpoint", DEFAULT_RERANK_URL)
    return os.getenv("RERANK_SERVER") or DEFAULT_RERANK_URL


def truncate(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars]


def rerank(
    query: str,
    candidates: list[dict[str, Any]],
    *,
    endpoint: str | None = None,
    timeout: int = 60,
    truncate_chars: int = 1500,
    raw_scores: bool = False,
) -> list[dict[str, Any]]:
    """
    Rerank candidate hit dicts (must include ``text``).

    Returns new list sorted by reranker score (desc). Original fields kept;
    ``score`` becomes the reranker score; ``rrf_score`` preserved if present.
    """
    if not candidates:
        return []

    url = endpoint or DEFAULT_RERANK_URL
    texts = [truncate(c.get("text") or "", truncate_chars) for c in candidates]

    resp = requests.post(
        url,
        json={
            "query": query,
            "texts": texts,
            "raw_scores": raw_scores,
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    ranked = resp.json()

    # TEI returns [{"index": i, "score": s}, ...] already sorted by score desc
    out: list[dict[str, Any]] = []
    for item in ranked:
        idx = int(item["index"])
        if idx < 0 or idx >= len(candidates):
            continue
        hit = dict(candidates[idx])
        hit["score"] = float(item["score"])
        hit["rerank_score"] = float(item["score"])
        hit["retriever"] = "rerank"
        out.append(hit)
    return out
