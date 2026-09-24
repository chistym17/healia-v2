"""Read local FAISS + metadata.jsonl for Qdrant upload."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

import faiss
import numpy as np

BACKEND = Path(__file__).resolve().parents[1]
ASSESSMENT_STORE = BACKEND / "medical_rag" / "assessment" / "store"
KNOWLEDGE_STORE = BACKEND / "medical_rag" / "store"


def _l2_normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-12)
    return (vectors / norms).astype(np.float32)


def load_faiss(store_dir: Path) -> faiss.Index:
    path = store_dir / "index.faiss"
    if not path.is_file():
        raise FileNotFoundError(f"Missing FAISS index: {path}")
    return faiss.read_index(str(path))


def iter_metadata(store_dir: Path) -> Iterator[dict[str, Any]]:
    path = store_dir / "metadata.jsonl"
    if not path.is_file():
        raise FileNotFoundError(f"Missing metadata: {path}")
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def count_metadata(store_dir: Path) -> int:
    return sum(1 for _ in iter_metadata(store_dir))


def assessment_payload(row: dict[str, Any]) -> dict[str, Any]:
    meta = row.get("metadata") or {}
    answer = str(row.get("answer") or "")
    if len(answer) > 8000:
        answer = answer[:8000]
    return {
        "doc_id": row.get("id") or "",
        "row": int(row.get("row") or 0),
        "topic": row.get("topic") or meta.get("topic") or "",
        "question": row.get("question") or meta.get("question") or "",
        "answer": answer,
        "text": row.get("text") or "",
        "question_type": str(meta.get("question_type") or "general"),
        "origin": str(meta.get("origin") or ""),
        "url": str(meta.get("url") or ""),
        "document_id": str(meta.get("document_id") or ""),
        "synonyms": meta.get("synonyms") or [],
    }


def knowledge_payload(row: dict[str, Any]) -> dict[str, Any]:
    meta = row.get("metadata") or {}
    # Keep payload lean but useful for grounding.
    flat_meta = {
        k: v
        for k, v in meta.items()
        if isinstance(v, (str, int, float, bool)) or v is None
    }
    text = str(row.get("text") or "")
    if len(text) > 8000:
        text = text[:8000]
    return {
        "doc_id": row.get("id") or "",
        "row": int(row.get("row") or 0),
        "source": row.get("source") or "",
        "text": text,
        "metadata": flat_meta,
    }


def iter_point_batches(
    store_dir: Path,
    *,
    payload_fn,
    batch_size: int = 128,
) -> Iterator[tuple[list[int], list[list[float]], list[dict[str, Any]]]]:
    """Yield (ids, vectors, payloads) batches. Point id = FAISS row index."""
    index = load_faiss(store_dir)
    meta_rows = list(iter_metadata(store_dir))
    if index.ntotal != len(meta_rows):
        raise RuntimeError(
            f"FAISS ntotal={index.ntotal} != metadata={len(meta_rows)} in {store_dir}"
        )

    total = index.ntotal
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        # reconstruct_n is efficient for IndexFlat*
        vecs = np.empty((end - start, index.d), dtype=np.float32)
        for i, row in enumerate(range(start, end)):
            vecs[i] = index.reconstruct(row)
        vecs = _l2_normalize(vecs)

        ids = list(range(start, end))
        payloads = [payload_fn(meta_rows[i]) for i in ids]
        vectors = vecs.tolist()
        yield ids, vectors, payloads
