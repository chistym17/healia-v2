"""
Healia ↔ Qdrant Cloud.

Env (backend/.env):
  VECTOR_BACKEND=local|qdrant   (default: local)
  QDRANT_URL
  QDRANT_API_KEY
  QDRANT_TIMEOUT_SEC  (optional, default 30)

Commands (from backend/):
  python -m qdrant
  python -m qdrant.upload assessment --recreate          # dense-only (legacy)
  python -m qdrant.upload knowledge --recreate           # dense-only (legacy)
  python -m qdrant.upload_hybrid assessment --recreate   # dense + BM25 sparse
  python -m qdrant.upload_hybrid knowledge --recreate
"""

from qdrant.client import get_client, ping, reset_client
from qdrant.config import (
    ASSESSMENT_COLLECTION,
    KNOWLEDGE_COLLECTION,
    VECTOR_SIZE,
    is_configured,
    vector_backend,
)

__all__ = [
    "ASSESSMENT_COLLECTION",
    "KNOWLEDGE_COLLECTION",
    "VECTOR_SIZE",
    "get_client",
    "is_configured",
    "ping",
    "reset_client",
    "vector_backend",
]
