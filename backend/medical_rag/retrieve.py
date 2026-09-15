"""
Medical corpus retrieval: FAISS, BM25, hybrid (RRF), or hybrid + BGE rerank.

Does not modify embeddings or the FAISS index.
"""

from __future__ import annotations

import json
import os
import pickle
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import faiss
import numpy as np
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reranker import is_rerank_enabled, rerank, resolve_rerank_url

CONFIG_PATH = ROOT / "config.json"
TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def truncate_for_embed(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars]


def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-12)
    return (vectors / norms).astype(np.float32)


def rrf_fuse(
    ranked_lists: list[list[dict[str, Any]]],
    rrf_k: float = 60.0,
    top_k: int = 30,
) -> list[dict[str, Any]]:
    """Reciprocal Rank Fusion over lists of hit dicts keyed by id."""
    scores: dict[str, float] = defaultdict(float)
    best: dict[str, dict[str, Any]] = {}

    for hits in ranked_lists:
        for rank, hit in enumerate(hits, start=1):
            doc_id = hit["id"]
            scores[doc_id] += 1.0 / (rrf_k + rank)
            prev = best.get(doc_id)
            if prev is None or float(hit.get("score", 0.0)) > float(
                prev.get("score", 0.0)
            ):
                best[doc_id] = hit

    ordered = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    fused: list[dict[str, Any]] = []
    for doc_id, rrf_score in ordered:
        hit = dict(best[doc_id])
        hit["score"] = float(rrf_score)
        hit["rrf_score"] = float(rrf_score)
        fused.append(hit)
    return fused


def build_offsets(metadata_path: Path) -> list[int]:
    offsets: list[int] = []
    with metadata_path.open("rb") as f:
        while True:
            pos = f.tell()
            line = f.readline()
            if not line:
                break
            if line.strip():
                offsets.append(pos)
    return offsets


class MedicalRetriever:
    """FAISS / BM25 / hybrid retriever over the medical corpus."""

    def __init__(self, root: Path | None = None, load_bm25: bool = True):
        self.root = root or ROOT
        self.cfg = load_json(self.root / "config.json")
        self.store_dir = (self.root / self.cfg["paths"]["store_dir"]).resolve()
        self.bm25_dir = (self.root / self.cfg["paths"]["bm25_dir"]).resolve()

        self.metadata_path = self.store_dir / "metadata.jsonl"
        index_path = self.store_dir / "index.faiss"
        store_cfg_path = self.store_dir / "config.json"

        for p in (self.metadata_path, index_path, store_cfg_path):
            if not p.is_file():
                raise FileNotFoundError(f"Missing store artifact: {p}")

        self.store_cfg = load_json(store_cfg_path)
        self.emb_cfg = self.store_cfg["embedding"]
        self.endpoint = self._resolve_endpoint()
        self.rerank_endpoint = resolve_rerank_url(self.cfg)

        self.faiss_index = faiss.read_index(str(index_path))
        self.offsets = build_offsets(self.metadata_path)
        if self.faiss_index.ntotal != len(self.offsets):
            raise RuntimeError(
                f"FAISS ntotal={self.faiss_index.ntotal} != "
                f"metadata rows={len(self.offsets)}"
            )

        self.bm25 = None
        self.bm25_doc_ids: list[str] | None = None
        if load_bm25:
            self._load_bm25()

    def _resolve_endpoint(self) -> str:
        load_dotenv(self.root.parent / ".env")
        emb = self.cfg["embedding"]
        return os.getenv(emb["endpoint_env"]) or emb["default_endpoint"]

    def _load_bm25(self) -> None:
        index_path = self.bm25_dir / "bm25.pkl"
        if not index_path.is_file():
            return
        with index_path.open("rb") as f:
            payload = pickle.load(f)
        self.bm25 = payload["bm25"]
        self.bm25_doc_ids = payload["doc_ids"]
        if len(self.bm25_doc_ids) != len(self.offsets):
            raise RuntimeError(
                f"BM25 docs={len(self.bm25_doc_ids)} != "
                f"metadata rows={len(self.offsets)}. Rebuild BM25."
            )

    def require_bm25(self) -> None:
        if self.bm25 is None:
            raise FileNotFoundError(
                f"BM25 index not found in {self.bm25_dir}. "
                "Run: python medical_rag/build_bm25.py"
            )

    def metadata_at(self, row: int) -> dict[str, Any]:
        with self.metadata_path.open("rb") as f:
            f.seek(self.offsets[row])
            return json.loads(f.readline().decode("utf-8"))

    def embed_query(self, text: str) -> np.ndarray:
        payload = {
            "inputs": [
                truncate_for_embed(
                    text, int(self.emb_cfg.get("truncate_chars", 900))
                )
            ]
        }
        resp = requests.post(
            self.endpoint,
            json=payload,
            timeout=self.emb_cfg.get("request_timeout_sec", 60),
        )
        resp.raise_for_status()
        return l2_normalize(np.asarray(resp.json(), dtype=np.float32))

    def search_faiss(self, query: str, top_k: int = 20) -> list[dict[str, Any]]:
        q = self.embed_query(query)
        scores, indices = self.faiss_index.search(q, top_k)
        hits: list[dict[str, Any]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            meta = self.metadata_at(int(idx))
            hits.append(
                {
                    "id": meta["id"],
                    "row": int(meta["row"]),
                    "source": meta.get("source"),
                    "text": meta.get("text"),
                    "metadata": meta.get("metadata") or {},
                    "score": float(score),
                    "retriever": "faiss",
                }
            )
        return hits

    def search_bm25(self, query: str, top_k: int = 20) -> list[dict[str, Any]]:
        self.require_bm25()
        assert self.bm25 is not None and self.bm25_doc_ids is not None

        tokens = tokenize(query)
        if not tokens:
            return []

        scores = self.bm25.get_scores(tokens)
        if top_k >= len(scores):
            top_idx = np.argsort(scores)[::-1]
        else:
            # argpartition then sort the top slice
            part = np.argpartition(scores, -top_k)[-top_k:]
            top_idx = part[np.argsort(scores[part])[::-1]]

        hits: list[dict[str, Any]] = []
        for idx in top_idx:
            idx = int(idx)
            if scores[idx] <= 0:
                continue
            meta = self.metadata_at(idx)
            if meta["id"] != self.bm25_doc_ids[idx]:
                raise RuntimeError(
                    f"BM25/metadata id mismatch at row {idx}: "
                    f"{meta['id']} vs {self.bm25_doc_ids[idx]}"
                )
            hits.append(
                {
                    "id": meta["id"],
                    "row": int(meta["row"]),
                    "source": meta.get("source"),
                    "text": meta.get("text"),
                    "metadata": meta.get("metadata") or {},
                    "score": float(scores[idx]),
                    "retriever": "bm25",
                }
            )
        return hits

    def search_hybrid(
        self,
        query: str,
        top_k: int | None = None,
        faiss_top_k: int | None = None,
        bm25_top_k: int | None = None,
        rrf_k: float | None = None,
    ) -> list[dict[str, Any]]:
        hy = self.cfg.get("hybrid", {})
        faiss_top_k = faiss_top_k or int(hy.get("faiss_top_k", 20))
        bm25_top_k = bm25_top_k or int(hy.get("bm25_top_k", 20))
        rrf_k = float(rrf_k if rrf_k is not None else hy.get("rrf_k", 60))
        top_k = top_k or int(hy.get("candidate_k", 30))

        faiss_hits = self.search_faiss(query, top_k=faiss_top_k)
        bm25_hits = self.search_bm25(query, top_k=bm25_top_k)
        fused = rrf_fuse([faiss_hits, bm25_hits], rrf_k=rrf_k, top_k=top_k)
        for hit in fused:
            hit["retriever"] = "hybrid"
        return fused

    def search_rerank(
        self,
        query: str,
        top_k: int = 10,
        candidate_k: int | None = None,
    ) -> list[dict[str, Any]]:
        """Hybrid candidates → BGE reranker → top_k."""
        rr = self.cfg.get("reranker", {})
        candidate_k = candidate_k or int(rr.get("candidate_k", 30))
        # Pull a candidate pool at least as large as top_k
        pool_k = max(candidate_k, top_k)

        candidates = self.search_hybrid(query, top_k=pool_k)
        ranked = rerank(
            query,
            candidates,
            endpoint=self.rerank_endpoint,
            timeout=int(rr.get("request_timeout_sec", 60)),
            truncate_chars=int(rr.get("truncate_chars", 1500)),
        )
        return ranked[:top_k]

    def search(
        self,
        query: str,
        mode: str = "hybrid",
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        mode = mode.lower().strip()
        if mode == "faiss":
            return self.search_faiss(query, top_k=top_k)
        if mode == "bm25":
            return self.search_bm25(query, top_k=top_k)
        if mode == "hybrid":
            return self.search_hybrid(query, top_k=top_k)
        if mode in ("rerank", "hybrid_rerank"):
            # Optional via RERANK_ENABLED=false → hybrid (no cross-encoder).
            if not is_rerank_enabled():
                return self.search_hybrid(query, top_k=top_k)
            return self.search_rerank(query, top_k=top_k)
        raise ValueError(
            f"Unknown mode {mode!r}; use faiss|bm25|hybrid|rerank"
        )