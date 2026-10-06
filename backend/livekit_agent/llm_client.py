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


def _is_json_mode_failure(exc: BaseException) -> bool:
    text = str(exc).lower()
    return (
        "json_validate_failed" in text
        or "failed to validate json" in text
        or "failed to generate json" in text
        or "max completion tokens reached before generating a valid document" in text
    )


async def _chat_completion(
    *,
    system: str,
    user: str,
    model: str,
    temperature: float,
    max_tokens: int | None,
    json_object: bool,
    reasoning_effort: str | None,
) -> str:
    client = get_groq_client()
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if json_object:
        kwargs["response_format"] = {"type": "json_object"}
    if reasoning_effort:
        kwargs["reasoning_effort"] = reasoning_effort

    try:
        completion = await client.chat.completions.create(**kwargs)
    except TypeError:
        # Older groq SDK without reasoning_effort
        kwargs.pop("reasoning_effort", None)
        completion = await client.chat.completions.create(**kwargs)

    choice = (completion.choices or [None])[0]
    if choice is None or choice.message is None:
        raise RuntimeError("empty Groq response")
    text = (choice.message.content or "").strip()
    if not text:
        raise RuntimeError("empty Groq message content")
    return text


async def groq_json_completion(
    *,
    system: str,
    user: str,
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int | None = None,
    reasoning_effort: str | None = None,
) -> str:
    """Chat completion with JSON object mode. Returns raw text content."""
    return await _chat_completion(
        system=system,
        user=user,
        model=model or config.SUPERVISOR_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
        json_object=True,
        reasoning_effort=reasoning_effort,
    )


async def groq_text_completion(
    *,
    system: str,
    user: str,
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int | None = None,
    reasoning_effort: str | None = None,
) -> str:
    """Chat completion without JSON mode (caller parses)."""
    return await _chat_completion(
        system=system,
        user=user,
        model=model or config.SUPERVISOR_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
        json_object=False,
        reasoning_effort=reasoning_effort,
    )


async def groq_json_with_text_fallback(
    *,
    system: str,
    user: str,
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int | None = None,
    reasoning_effort: str | None = None,
) -> tuple[str, str]:
    """
    Try JSON object mode first; on Groq JSON validation / token-cutoff errors,
    retry once without JSON mode so the caller can extract JSON from text.

    Returns (content, mode) where mode is "json_object" or "text_fallback".
    """
    model_id = model or config.SUPERVISOR_MODEL
    try:
        text = await groq_json_completion(
            system=system,
            user=user,
            model=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort,
        )
        return text, "json_object"
    except Exception as exc:
        if not _is_json_mode_failure(exc):
            raise
        text = await groq_text_completion(
            system=system,
            user=user,
            model=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort or "low",
        )
        return text, "text_fallback"
