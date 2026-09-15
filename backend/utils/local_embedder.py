"""Backward-compatible embedding helpers. Prefer utils.embeddings. """

from utils.embeddings import embed_query, embed_texts, get_embedding

__all__ = ["get_embedding", "embed_query", "embed_texts"]
