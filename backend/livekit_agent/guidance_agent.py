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
- Results sections must be clear, calm, and scannable for a Results page.
- possible_concerns must sound uncertain (may be / possible), never a confirmed diagnosis.
- actions must be practical self-care steps only (no prescriptions or doses).
- warning_signs and seek_care must be present whenever clinically relevant; otherwise give
  sensible general advice to seek care if symptoms worsen.
- Output JSON only, matching this schema exactly:

{
  "spoken_answer": "string",
  "detailed_answer": "string",
  "summary": "string",
  "possible_concerns": "string",
  "actions": ["string"],
  "warning_signs": "string",
  "seek_care": "string",
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


def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            items.append(text)
    return items


def parse_guidance_response(payload: dict[str, Any]) -> dict[str, Any]:
    spoken = str(payload.get("spoken_answer") or "").strip()
    detailed = str(payload.get("detailed_answer") or "").strip()
    summary = str(payload.get("summary") or "").strip()
    possible_concerns = str(payload.get("possible_concerns") or "").strip()
    warning_signs = str(payload.get("warning_signs") or "").strip()
    seek_care = str(payload.get("seek_care") or "").strip()
    actions = _as_str_list(payload.get("actions"))
    citations = payload.get("citations") or []
    if not isinstance(citations, list):
        citations = []
    confidence = str(payload.get("confidence") or "medium").strip().lower()
    if confidence not in ("low", "medium", "high"):
        confidence = "medium"

    # Fallbacks so Results UI is never empty when model omits sections.
    if not summary:
        summary = detailed or spoken
    if not possible_concerns:
        possible_concerns = detailed or spoken
    if not seek_care:
        seek_care = (
            "See a qualified clinician if symptoms persist, worsen, or you are unsure. "
            "For emergency symptoms, seek urgent care immediately."
        )
    if not warning_signs:
        warning_signs = (
            "Seek urgent care for severe or sudden symptoms, difficulty breathing, "
            "chest pain, confusion, fainting, or rapidly worsening condition."
        )
    if not actions:
        actions = [
            "Rest and monitor your symptoms",
            "Stay hydrated",
            "Seek medical care if symptoms worsen",
        ]

    return {
        "spoken_answer": spoken,
        "detailed_answer": detailed or spoken,
        "summary": summary,
        "possible_concerns": possible_concerns,
        "actions": actions,
        "warning_signs": warning_signs,
        "seek_care": seek_care,
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
            "summary": "",
            "possible_concerns": "",
            "actions": [],
            "warning_signs": "",
            "seek_care": "",
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
