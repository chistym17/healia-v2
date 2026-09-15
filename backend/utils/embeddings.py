"""
Query embedding client.

Providers (EMBEDDING_PROVIDER):
  - local (default): TEI-compatible server via EMBEDDING_SERVER
  - huggingface: hosted MiniLM via Hugging Face Inference API

Indexes were built with sentence-transformers/all-MiniLM-L6-v2 (384-d).
Keep that model for any hosted provider so FAISS stays valid.
"""

from __future__ import annotations

import os
import time
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_LOCAL_ENDPOINT = "http://localhost:8080/embed"
HF_FEATURE_URL = (
    "https://router.huggingface.co/hf-inference/models/"
    "{model}/pipeline/feature-extraction"
)


def embedding_provider() -> str:
    raw = (os.getenv("EMBEDDING_PROVIDER") or "local").strip().lower()
    if raw in ("hf", "hugging_face", "huggingface_hub"):
        return "huggingface"
    return raw or "local"


def embedding_model() -> str:
    return (
        os.getenv("EMBEDDING_MODEL")
        or os.getenv("HF_EMBEDDING_MODEL")
        or DEFAULT_MODEL
    ).strip()


def _hf_token() -> str:
    return (
        os.getenv("HF_TOKEN")
        or os.getenv("HUGGINGFACE_API_KEY")
        or os.getenv("HUGGINGFACE_HUB_TOKEN")
        or ""
    ).strip()


def _local_endpoint() -> str:
    return (
        os.getenv("EMBEDDING_SERVER") or DEFAULT_LOCAL_ENDPOINT
    ).strip()


def _truncate(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars]


def _as_vectors(payload: Any) -> list[list[float]]:
    """Normalize TEI / HF JSON into a list of embedding vectors."""
    if payload is None:
        raise ValueError("Empty embedding response")

    # Single vector: [d]
    if isinstance(payload, list) and payload and isinstance(payload[0], (int, float)):
        return [[float(x) for x in payload]]

    # Batch of vectors: [[d], ...]
    if isinstance(payload, list) and payload and isinstance(payload[0], list):
        first = payload[0]
        # Token-level matrix for one input: [[tokens], dim] → mean-pool
        if first and isinstance(first[0], list):
            vectors: list[list[float]] = []
            for matrix in payload:
                rows = [[float(x) for x in row] for row in matrix]
                dim = len(rows[0])
                pooled = [0.0] * dim
                for row in rows:
                    for i, val in enumerate(row):
                        pooled[i] += val
                n = float(len(rows)) or 1.0
                vectors.append([v / n for v in pooled])
            return vectors
        return [[float(x) for x in row] for row in payload]

    raise ValueError(f"Unexpected embedding response shape: {type(payload)}")


def _embed_local(texts: list[str], *, timeout: float) -> list[list[float]]:
    endpoint = _local_endpoint()
    if not endpoint:
        raise RuntimeError("EMBEDDING_SERVER is not set for local embeddings")

    resp = requests.post(
        endpoint,
        json={"inputs": texts if len(texts) > 1 else texts[0]},
        timeout=timeout,
    )
    resp.raise_for_status()
    vectors = _as_vectors(resp.json())
    if len(texts) == 1 and len(vectors) == 1:
        return vectors
    # Some TEI builds always wrap a single input as one vector; batch may vary.
    if len(vectors) == len(texts):
        return vectors
    # Retry as explicit batch list if scalar form was used above.
    resp = requests.post(
        endpoint,
        json={"inputs": texts},
        timeout=timeout,
    )
    resp.raise_for_status()
    vectors = _as_vectors(resp.json())
    if len(vectors) != len(texts):
        raise RuntimeError(
            f"Local embedder returned {len(vectors)} vectors for {len(texts)} inputs"
        )
    return vectors


def _embed_huggingface(texts: list[str], *, timeout: float) -> list[list[float]]:
    token = _hf_token()
    if not token:
        raise RuntimeError(
            "EMBEDDING_PROVIDER=huggingface requires HF_TOKEN "
            "(or HUGGINGFACE_API_KEY)"
        )

    model = embedding_model()
    url = (
        os.getenv("HF_EMBEDDING_URL")
        or HF_FEATURE_URL.format(model=model)
    ).strip()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Free serverless can cold-start; retry a few times on 503.
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            resp = requests.post(
                url,
                headers=headers,
                json={"inputs": texts if len(texts) > 1 else texts[0]},
                timeout=timeout,
            )
            if resp.status_code == 503:
                time.sleep(min(2 ** attempt, 8))
                continue
            resp.raise_for_status()
            vectors = _as_vectors(resp.json())
            if len(vectors) == len(texts):
                return vectors
            if len(texts) == 1 and len(vectors) == 1:
                return vectors
            # Fall through to batch form
            resp = requests.post(
                url,
                headers=headers,
                json={"inputs": texts},
                timeout=timeout,
            )
            if resp.status_code == 503:
                time.sleep(min(2 ** attempt, 8))
                continue
            resp.raise_for_status()
            vectors = _as_vectors(resp.json())
            if len(vectors) != len(texts):
                raise RuntimeError(
                    f"HF embedder returned {len(vectors)} vectors for {len(texts)} inputs"
                )
            return vectors
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(min(2 ** attempt, 8))

    raise RuntimeError(
        f"Hugging Face embedding failed after retries: {last_error}"
    )


def embed_texts(
    texts: list[str],
    *,
    truncate_chars: int = 900,
    timeout: float | None = None,
) -> list[list[float]]:
    """Embed one or more texts. Returns L2-ready raw vectors (not normalized)."""
    cleaned = [_truncate(t.strip(), truncate_chars) for t in texts if t is not None]
    cleaned = [t if t else " " for t in cleaned]
    if not cleaned:
        return []

    provider = embedding_provider()
    wait = float(timeout if timeout is not None else os.getenv("EMBEDDING_TIMEOUT_SEC") or 30)

    if provider == "huggingface":
        return _embed_huggingface(cleaned, timeout=wait)
    if provider == "local":
        return _embed_local(cleaned, timeout=wait)
    raise RuntimeError(
        f"Unknown EMBEDDING_PROVIDER={provider!r}. Use 'local' or 'huggingface'."
    )


def embed_query(
    text: str,
    *,
    truncate_chars: int = 900,
    timeout: float | None = None,
) -> list[float]:
    """Embed a single query string."""
    vectors = embed_texts(
        [text],
        truncate_chars=truncate_chars,
        timeout=timeout,
    )
    if not vectors:
        return []
    return vectors[0]


# Backward-compatible name used by older workflow code.
def get_embedding(text: str) -> list[float]:
    try:
        return embed_query(text)
    except Exception as exc:
        print("Embedding error:", exc)
        return []
