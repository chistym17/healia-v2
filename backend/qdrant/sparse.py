"""BM25-style sparse vectors for Qdrant (server-side IDF)."""

from __future__ import annotations

import hashlib
import re
from collections import Counter

TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall((text or "").lower())


def term_id(token: str) -> int:
    """Stable uint32 index for a token (same across processes)."""
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=4).digest()
    return int.from_bytes(digest, "big")


def text_to_sparse(text: str):
    """Term-frequency SparseVector. Qdrant applies IDF when modifier=IDF."""
    from qdrant_client.models import SparseVector

    counts = Counter(tokenize(text))
    if not counts:
        return SparseVector(indices=[], values=[])

    # Collapse rare hash collisions by summing TFs.
    merged: dict[int, float] = {}
    for token, tf in counts.items():
        idx = term_id(token)
        merged[idx] = merged.get(idx, 0.0) + float(tf)

    indices = sorted(merged.keys())
    values = [merged[i] for i in indices]
    return SparseVector(indices=indices, values=values)
