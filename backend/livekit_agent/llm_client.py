"""Groq text LLM client for supervisor + guidance (OpenAI GPT-OSS)."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from livekit_agent import config


@lru_cache(maxsize=1)
def get_groq_client():
    """Process-wide AsyncGroq client."""
    from groq import AsyncGroq

    api_key = (os.getenv("GROQ_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")
    return AsyncGroq(api_key=api_key)


async def groq_json_completion(
    *,
    system: str,
    user: str,
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int | None = None,
) -> str:
    """Chat completion with JSON object mode. Returns raw text content."""
    client = get_groq_client()
    kwargs: dict[str, Any] = {
        "model": model or config.SUPERVISOR_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    completion = await client.chat.completions.create(**kwargs)
    choice = (completion.choices or [None])[0]
    if choice is None or choice.message is None:
        raise RuntimeError("empty Groq response")
    text = (choice.message.content or "").strip()
    if not text:
        raise RuntimeError("empty Groq message content")
    return text
