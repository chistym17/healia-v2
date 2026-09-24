"""Qdrant env + collection constants."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# MiniLM indexes → 384-d cosine / IP (we L2-normalize queries)
VECTOR_SIZE = 384

KNOWLEDGE_COLLECTION = "healia_knowledge"
ASSESSMENT_COLLECTION = "healia_assessment"


def url() -> str:
    return (os.getenv("QDRANT_URL") or "").strip().rstrip("/")


def api_key() -> str:
    return (os.getenv("QDRANT_API_KEY") or "").strip()


def timeout_sec() -> int:
    raw = (os.getenv("QDRANT_TIMEOUT_SEC") or "30").strip()
    try:
        return max(5, int(raw))
    except ValueError:
        return 30


def is_configured() -> bool:
    return bool(url() and api_key())


def url_host() -> str:
    raw = url()
    if not raw:
        return ""
    return raw.split("//")[-1].split("/")[0]
