"""
Healia ↔ Qdrant Cloud.

Env (backend/.env):
  QDRANT_URL
  QDRANT_API_KEY
  QDRANT_TIMEOUT_SEC  (optional, default 30)

Smoke test:
  cd backend && PYTHONPATH=venv/lib/python3.12/site-packages:$PWD python -m qdrant
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
