"""
Healia ↔ Qdrant Cloud.

Env (backend/.env):
  QDRANT_URL
  QDRANT_API_KEY
  QDRANT_TIMEOUT_SEC  (optional, default 30)

Commands (from backend/):
  python -m qdrant
  python -m qdrant.upload assessment --recreate
  python -m qdrant.upload knowledge --recreate
"""

from qdrant.client import get_client, ping, reset_client
from qdrant.config import (
    ASSESSMENT_COLLECTION,
    KNOWLEDGE_COLLECTION,
    VECTOR_SIZE,
    is_configured,
)

__all__ = [
    "ASSESSMENT_COLLECTION",
    "KNOWLEDGE_COLLECTION",
    "VECTOR_SIZE",
    "get_client",
    "is_configured",
    "ping",
    "reset_client",
]
