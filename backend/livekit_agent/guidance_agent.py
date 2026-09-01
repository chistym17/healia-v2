"""Grounded guidance generation from medical RAG chunks (Gemini JSON)."""

from __future__ import annotations

import json
import re
from typing import Any

from google.genai import types

from livekit_agent import config
from livekit_agent.supervisor import get_supervisor_client

_SYSTEM_PROMPT = """
You are Healia's medical knowledge assistant (backend). You turn retrieved reference
excerpts into patient-facing educational guidance. This is NOT a medical diagnosis.

Rules:
- Use ONLY the provided reference excerpts. If they are insufficient, say so briefly.
- Do not prescribe medications, doses, or specific treatment plans.
- Encourage professional care for serious, worsening, or uncertain symptoms.
- Cite excerpts inline as [1], [2], etc., matching excerpt numbers.
- spoken_answer must be natural for voice: 2-3 short sentences, under 60 words.
- Output JSON only, matching this schema exactly:

{
  "spoken_answer": "string",
  "detailed_answer": "string",
  "citations": [
    {"index": 1, "source": "statpearls|medquad", "topic": "string", "section": "string"}
  ],
  "confidence": "low|medium|high"
}
""".strip()


def _extract_json(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        raise ValueError("empty guidance response")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def format_chunk_for_prompt(hit: dict[str, Any], index: int) -> str:
    meta = hit.get("metadata") or {}
    topic = str(meta.get("topic") or meta.get("name") or "Unknown").strip()
    section = str(meta.get("section") or "").strip()
    source = str(hit.get("source") or "unknown").strip()
    text = str(hit.get("text") or "").strip()
    header = f"[{index}] Source: {source} | Topic: {topic}"
    if section:
        header += f" | Section: {section}"
    return f"{header}\n{text}"


def build_user_prompt(
    *,
    final_query: str,
    chief_complaint: str | None,
    facts: dict[str, Any] | None,
    chunks: list[dict[str, Any]],
) -> str:
    excerpt_blocks = [
        format_chunk_for_prompt(hit, i + 1) for i, hit in enumerate(chunks)
    ]
    payload = {
        "final_query": final_query,
        "chief_complaint": chief_complaint,
        "known_facts": facts or {},
        "reference_excerpts": excerpt_blocks,
    }
    return json.dumps(payload, ensure_ascii=False)


def parse_guidance_response(payload: dict[str, Any]) -> dict[str, Any]:
    spoken = str(payload.get("spoken_answer") or "").strip()
    detailed = str(payload.get("detailed_answer") or "").strip()
    citations = payload.get("citations") or []
    if not isinstance(citations, list):
        citations = []
    confidence = str(payload.get("confidence") or "medium").strip().lower()
    if confidence not in ("low", "medium", "high"):
        confidence = "medium"

    return {
        "spoken_answer": spoken,
        "detailed_answer": detailed or spoken,
        "citations": citations,
        "confidence": confidence,
        "raw": payload,
    }


async def generate_guidance(
    *,
    final_query: str,
    chief_complaint: str | None,
    facts: dict[str, Any] | None,
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """Call Gemini to produce voice-friendly grounded guidance."""
    if not chunks:
        return {
            "spoken_answer": "",
            "detailed_answer": "",
            "citations": [],
            "confidence": "low",
            "error": "no_chunks",
            "raw": {},
        }

    user_prompt = build_user_prompt(
        final_query=final_query,
        chief_complaint=chief_complaint,
        facts=facts,
        chunks=chunks,
    )

    client = get_supervisor_client()
    response = await client.aio.models.generate_content(
        model=config.GUIDANCE_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            temperature=config.GUIDANCE_TEMPERATURE,
            response_mime_type="application/json",
            max_output_tokens=config.GUIDANCE_MAX_OUTPUT_TOKENS,
        ),
    )
    text = (response.text or "").strip()
    parsed = parse_guidance_response(_extract_json(text))
    parsed["error"] = None
    return parsed
