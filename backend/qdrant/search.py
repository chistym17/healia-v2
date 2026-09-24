"""Query Qdrant hybrid collections (dense + sparse BM25)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from dotenv import load_dotenv

from qdrant import config
from qdrant.client import get_client
from qdrant.sparse import text_to_sparse

BACKEND = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND / ".env")

KNOWLEDGE_CFG = BACKEND / "medical_rag" / "config.json"
ASSESSMENT_CFG = BACKEND / "medical_rag" / "assessment" / "config.json"


def _l2_normalize(vector: list[float]) -> list[float]:
    arr = np.asarray(vector, dtype=np.float32)
    norm = float(np.linalg.norm(arr))
    if norm < 1e-12:
        return arr.tolist()
    return (arr / norm).astype(np.float32).tolist()


def _embed(text: str, *, truncate_chars: int = 900, timeout: float = 60.0) -> list[float]:
    from utils.embeddings import embed_query

    vector = embed_query(text, truncate_chars=truncate_chars, timeout=timeout)
    if not vector:
        raise RuntimeError("Embedding provider returned an empty vector")
    return _l2_normalize(vector)


def _knowledge_hit(point, *, retriever: str) -> dict[str, Any]:
    payload = point.payload or {}
    return {
        "id": payload.get("doc_id") or str(point.id),
        "row": int(payload.get("row") or point.id or 0),
        "source": payload.get("source"),
        "text": payload.get("text"),
        "metadata": payload.get("metadata") or {},
        "score": float(point.score or 0.0),
        "retriever": retriever,
    }


def _query_points(
    collection: str,
    *,
    dense: list[float] | None = None,
    sparse=None,
    mode: str,
    top_k: int,
    dense_k: int = 20,
    sparse_k: int = 20,
):
    from qdrant_client.models import Fusion, FusionQuery, Prefetch

    client = get_client()
    mode = mode.lower().strip()

    if mode in ("faiss", "dense"):
        if dense is None:
            raise ValueError("dense vector required")
        return client.query_points(
            collection_name=collection,
            query=dense,
            using=config.DENSE_VECTOR,
            limit=top_k,
            with_payload=True,
        ).points

    if mode == "bm25":
        if sparse is None:
            raise ValueError("sparse vector required")
        return client.query_points(
            collection_name=collection,
            query=sparse,
            using=config.SPARSE_VECTOR,
            limit=top_k,
            with_payload=True,
        ).points

    # hybrid / rerank candidate pool
    if dense is None or sparse is None:
        raise ValueError("dense and sparse vectors required for hybrid")
    return client.query_points(
        collection_name=collection,
        prefetch=[
            Prefetch(query=dense, using=config.DENSE_VECTOR, limit=dense_k),
            Prefetch(query=sparse, using=config.SPARSE_VECTOR, limit=sparse_k),
        ],
        query=FusionQuery(fusion=Fusion.RRF),
        limit=top_k,
        with_payload=True,
    ).points


def search_knowledge(
    query: str,
    *,
    mode: str = "hybrid",
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Same hit shape as MedicalRetriever.search()."""
    from medical_rag.reranker import is_rerank_enabled, rerank, resolve_rerank_url

    mode = (mode or "hybrid").lower().strip()
    cfg = json.loads(KNOWLEDGE_CFG.read_text(encoding="utf-8"))
    emb = cfg.get("embedding", {})
    hy = cfg.get("hybrid", {})
    rr = cfg.get("reranker", {})

    dense = _embed(
        query,
        truncate_chars=int(emb.get("truncate_chars", 900)),
        timeout=float(emb.get("request_timeout_sec", 60)),
    )
    sparse = text_to_sparse(query)

    if mode in ("rerank", "hybrid_rerank"):
        if not is_rerank_enabled():
            mode = "hybrid"
        else:
            pool_k = max(int(rr.get("candidate_k", 30)), top_k)
            points = _query_points(
                config.KNOWLEDGE_COLLECTION,
                dense=dense,
                sparse=sparse,
                mode="hybrid",
                top_k=pool_k,
                dense_k=int(hy.get("faiss_top_k", 20)),
                sparse_k=int(hy.get("bm25_top_k", 20)),
            )
            candidates = [_knowledge_hit(p, retriever="hybrid") for p in points]
            ranked = rerank(
                query,
                candidates,
                endpoint=resolve_rerank_url(cfg),
                timeout=int(rr.get("request_timeout_sec", 60)),
                truncate_chars=int(rr.get("truncate_chars", 1500)),
            )
            return ranked[:top_k]

    search_mode = "faiss" if mode == "faiss" else mode
    if search_mode not in ("faiss", "bm25", "hybrid"):
        raise ValueError(f"Unknown mode {mode!r}; use faiss|bm25|hybrid|rerank")

    points = _query_points(
        config.KNOWLEDGE_COLLECTION,
        dense=dense,
        sparse=sparse,
        mode=search_mode,
        top_k=top_k,
        dense_k=int(hy.get("faiss_top_k", 20)),
        sparse_k=int(hy.get("bm25_top_k", 20)),
    )
    label = "faiss" if search_mode == "faiss" else search_mode
    return [_knowledge_hit(p, retriever=label) for p in points]


def search_assessment_raw(query: str, *, top_k: int = 30) -> list[dict[str, Any]]:
    """Dense search over assessment collection; returns payload rows + score."""
    cfg = json.loads(ASSESSMENT_CFG.read_text(encoding="utf-8"))
    emb = cfg.get("embedding", {})
    dense = _embed(
        query,
        truncate_chars=int(emb.get("truncate_chars", 900)),
        timeout=float(emb.get("request_timeout_sec", 60)),
    )
    points = _query_points(
        config.ASSESSMENT_COLLECTION,
        dense=dense,
        mode="faiss",
        top_k=top_k,
    )
    hits: list[dict[str, Any]] = []
    for point in points:
        payload = point.payload or {}
        hits.append(
            {
                "id": payload.get("doc_id") or str(point.id),
                "row": int(payload.get("row") or point.id or 0),
                "topic": payload.get("topic") or "",
                "question": payload.get("question") or "",
                "answer": payload.get("answer") or "",
                "text": payload.get("text") or "",
                "question_type": str(payload.get("question_type") or "general"),
                "metadata": {
                    "question_type": payload.get("question_type") or "general",
                    "topic": payload.get("topic") or "",
                    "origin": payload.get("origin") or "",
                    "url": payload.get("url") or "",
                    "document_id": payload.get("document_id") or "",
                    "synonyms": payload.get("synonyms") or [],
                    "question": payload.get("question") or "",
                },
                "score": float(point.score or 0.0),
            }
        )
    return hits
