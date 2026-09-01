"""Knowledge retrieval over the StatPearls medical corpus (hybrid + rerank)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

_retriever_faiss_only = None
_retriever_full = None


def _needs_bm25(mode: str) -> bool:
    return mode.lower().strip() in ("bm25", "hybrid", "rerank", "hybrid_rerank")


def _get_retriever(*, load_bm25: bool):
    global _retriever_faiss_only, _retriever_full
    from medical_rag.retrieve import MedicalRetriever

    if load_bm25:
        if _retriever_full is None:
            _retriever_full = MedicalRetriever(load_bm25=True)
        return _retriever_full
    if _retriever_faiss_only is None:
        _retriever_faiss_only = MedicalRetriever(load_bm25=False)
    return _retriever_faiss_only


def retrieve_knowledge(
    query: str,
    *,
    mode: str = "rerank",
    top_k: int = 5,
) -> dict[str, Any]:
    """Retrieve grounded medical reference chunks for a final consultation query."""
    query = (query or "").strip()
    mode = (mode or "rerank").lower().strip()
    if not query:
        return {
            "source": "medical_rag",
            "query": query,
            "mode": mode,
            "chunks": [],
            "error": "empty_query",
        }

    effective_mode = mode
    fallback_note: str | None = None

    try:
        if _needs_bm25(mode):
            try:
                retriever = _get_retriever(load_bm25=True)
            except Exception as exc:
                retriever = _get_retriever(load_bm25=False)
                effective_mode = "faiss"
                fallback_note = f"bm25_unavailable: {exc}"
        else:
            retriever = _get_retriever(load_bm25=False)

        if effective_mode in ("rerank", "hybrid_rerank") and retriever.bm25 is None:
            effective_mode = "faiss"
            fallback_note = fallback_note or "bm25_index_missing"

        chunks = retriever.search(query, mode=effective_mode, top_k=top_k)
        result: dict[str, Any] = {
            "source": "medical_rag",
            "query": query,
            "mode": effective_mode,
            "requested_mode": mode,
            "chunks": chunks,
            "error": None,
        }
        if fallback_note:
            result["fallback"] = fallback_note
        return result
    except Exception as exc:
        return {
            "source": "medical_rag",
            "query": query,
            "mode": mode,
            "chunks": [],
            "error": str(exc),
        }
