from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any

from google import genai
from google.genai import types

from livekit_agent import config
from livekit_agent.events import log_event

ALLOWED_ACTIONS = frozenset(
    {
        "ask_followup",
        "acknowledge",
        "build_final_query",
        "escalate",
        "end",
    }
)

_SYSTEM_PROMPT = """
You are the Healia consultation supervisor (brain). You do NOT speak to the patient directly.
You read each completed patient turn and return ONE JSON decision for the voice agent.

Phase: gathering facts to build a final_query_draft (not a medical diagnosis).

Rules:
- Output JSON only, matching the schema exactly.
- One action per turn.
- spoken_utterance: short (1-2 sentences), one question max for ask_followup.
- Do not diagnose, prescribe, or give treatment plans.
- Extract facts from patient text into state_updates.new_facts when confident.
- Use state_updates.corrections when the patient fixes earlier info.
- For ask_followup, set followup_topic to a short snake_case key (e.g. headache_location).
- Do not ask about topics already in asked_topics unless correcting a fact.
- Prefer acknowledge when the patient only greets or gives no new medical info.
- Use build_final_query when you have enough for a coherent final_query_draft.
- Use escalate for emergency/red-flag language (chest pain, can't breathe, suicide, etc.).
- Follow-ups must be about THIS patient's complaint and latest answer. Name the complaint
  in spoken_utterance when useful (their headache / fever / cough — not "this" alone).
- Ask for the next missing useful detail. Prefer character of the problem first
  (where, when started, how strong, how it changed, key associated signs) before
  generic checklist items.
- Do NOT rotate the same generic quartet every consult (medications / past history /
  saw a doctor / what triggered it) unless those facts are still missing AND more
  complaint-specific details are already covered.
- If assessment_evidence.suggested_questions is present: treat each item as a THEME
  (theme / question_type / medical_topic). Do not read the hint question verbatim.
  Write a fresh spoken_utterance for this patient. Still one question max.
- English only.

JSON schema:
{
  "action": "ask_followup|acknowledge|build_final_query|escalate|end",
  "spoken_utterance": "string",
  "allow_light_paraphrase": true,
  "followup_topic": "optional snake_case, required for ask_followup",
  "state_updates": {
    "new_facts": {},
    "corrections": {},
    "chief_complaint": "optional string",
    "final_query_draft": "optional string",
    "phase": "optional gathering|ready|ended",
    "add_asked_topics": ["optional list of topics"]
  },
  "confidence": {"decision": 0.0},
  "reason": "short internal reason"
}
""".strip()


@dataclass
class SupervisorDecision:
    action: str
    spoken_utterance: str
    allow_light_paraphrase: bool
    followup_topic: str | None
    state_updates: dict[str, Any]
    confidence: float
    reason: str
    raw: dict[str, Any]


def _extract_json(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        raise ValueError("empty supervisor response")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def parse_supervisor_decision(payload: dict[str, Any]) -> SupervisorDecision:
    action = str(payload.get("action", "")).strip().lower()
    if action not in ALLOWED_ACTIONS:
        raise ValueError(f"unsupported action: {action}")

    spoken = str(payload.get("spoken_utterance", "")).strip()
    allow_para = bool(payload.get("allow_light_paraphrase", True))
    followup_topic = payload.get("followup_topic")
    if followup_topic is not None:
        followup_topic = str(followup_topic).strip() or None

    state_updates = payload.get("state_updates") or {}
    if not isinstance(state_updates, dict):
        raise ValueError("state_updates must be an object")

    confidence_block = payload.get("confidence") or {}
    confidence = 0.0
    if isinstance(confidence_block, dict):
        try:
            confidence = float(confidence_block.get("decision", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0

    reason = str(payload.get("reason", "")).strip()

    return SupervisorDecision(
        action=action,
        spoken_utterance=spoken,
        allow_light_paraphrase=allow_para,
        followup_topic=followup_topic,
        state_updates=state_updates,
        confidence=confidence,
        reason=reason,
        raw=payload,
    )


def _ms_since(t0: float) -> int:
    return int((time.monotonic() - t0) * 1000)


_client: genai.Client | None = None


def get_supervisor_client() -> genai.Client:
    """Process-wide reused GenAI client (created once per agent worker)."""
    global _client
    if _client is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY is not set")
        _client = genai.Client(api_key=api_key)
    return _client


async def warm_supervisor(*, session_id: str) -> None:
    """Fire a tiny discarded supervisor call while greeting runs (cuts turn-1 TTFB)."""
    if not config.SUPERVISOR_ENABLED:
        return
    t0 = time.monotonic()
    log_event(
        "SUP",
        "warmup_start",
        session_id=session_id,
        turn_id="warmup",
        detail=f"+0ms model={config.SUPERVISOR_MODEL}",
    )
    try:
        client = get_supervisor_client()
        log_event(
            "SUP",
            "client_ready",
            session_id=session_id,
            turn_id="warmup",
            detail=f"+{_ms_since(t0)}ms note=reused_or_created",
        )
        # Minimal payload; result discarded — only warms model/connection path.
        await client.aio.models.generate_content(
            model=config.SUPERVISOR_MODEL,
            contents='{"patient_turn":"hi","consultation_state":{"phase":"gathering","facts":{},"asked_topics":[]}}',
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                temperature=config.SUPERVISOR_TEMPERATURE,
                response_mime_type="application/json",
                max_output_tokens=64,
            ),
        )
        log_event(
            "SUP",
            "warmup_done",
            session_id=session_id,
            turn_id="warmup",
            detail=f"+{_ms_since(t0)}ms ok=true",
        )
    except Exception as exc:
        log_event(
            "SUP",
            "warmup_done",
            session_id=session_id,
            turn_id="warmup",
            detail=f"+{_ms_since(t0)}ms ok=false error={exc}",
        )


async def _generate_supervisor_text(
    client: genai.Client,
    *,
    user_prompt: str,
    session_id: str,
    turn_id: str,
    t0: float,
) -> str:
    """Call Gemini; prefer streaming so first_token vs complete can be split."""
    gen_config = types.GenerateContentConfig(
        system_instruction=_SYSTEM_PROMPT,
        temperature=config.SUPERVISOR_TEMPERATURE,
        response_mime_type="application/json",
    )

    stream_fn = getattr(client.aio.models, "generate_content_stream", None)
    if stream_fn is not None:
        log_event(
            "SUP",
            "request_sent",
            session_id=session_id,
            turn_id=turn_id,
            detail=f"+{_ms_since(t0)}ms model={config.SUPERVISOR_MODEL} mode=stream",
        )
        chunks: list[str] = []
        first_token_logged = False
        stream_result = stream_fn(
            model=config.SUPERVISOR_MODEL,
            contents=user_prompt,
            config=gen_config,
        )
        # google-genai may return a coroutine or an async iterator.
        if hasattr(stream_result, "__aiter__"):
            stream = stream_result
        else:
            stream = await stream_result
        async for chunk in stream:
            piece = getattr(chunk, "text", None) or ""
            if not piece:
                continue
            if not first_token_logged:
                first_token_logged = True
                log_event(
                    "SUP",
                    "first_token",
                    session_id=session_id,
                    turn_id=turn_id,
                    detail=f"+{_ms_since(t0)}ms chars={len(piece)}",
                )
            chunks.append(piece)
        text = "".join(chunks).strip()
        log_event(
            "SUP",
            "response_complete",
            session_id=session_id,
            turn_id=turn_id,
            detail=f"+{_ms_since(t0)}ms chars={len(text)}",
        )
        return text

    log_event(
        "SUP",
        "request_sent",
        session_id=session_id,
        turn_id=turn_id,
        detail=f"+{_ms_since(t0)}ms model={config.SUPERVISOR_MODEL} mode=unary",
    )
    response = await client.aio.models.generate_content(
        model=config.SUPERVISOR_MODEL,
        contents=user_prompt,
        config=gen_config,
    )
    text = (response.text or "").strip()
    # Unary: first byte and complete arrive together.
    log_event(
        "SUP",
        "first_token",
        session_id=session_id,
        turn_id=turn_id,
        detail=f"+{_ms_since(t0)}ms chars={len(text)} note=unary_same_as_complete",
    )
    log_event(
        "SUP",
        "response_complete",
        session_id=session_id,
        turn_id=turn_id,
        detail=f"+{_ms_since(t0)}ms chars={len(text)}",
    )
    return text


async def run_supervisor(
    *,
    patient_turn: str,
    state: dict[str, Any],
    session_id: str = "-",
    turn_id: str = "-",
    assessment_evidence: dict[str, Any] | None = None,
) -> SupervisorDecision:
    """Part 3A: same behavior; staged timing logs only."""
    t0 = time.monotonic()
    log_event(
        "SUP",
        "request_start",
        session_id=session_id,
        turn_id=turn_id,
        detail=f"+0ms model={config.SUPERVISOR_MODEL}",
    )

    payload_in: dict[str, Any] = {
        "patient_turn": patient_turn,
        "consultation_state": state,
    }
    if assessment_evidence is not None:
        payload_in["assessment_evidence"] = assessment_evidence

    user_prompt = json.dumps(payload_in, ensure_ascii=False)

    client = get_supervisor_client()
    log_event(
        "SUP",
        "client_ready",
        session_id=session_id,
        turn_id=turn_id,
        detail=f"+{_ms_since(t0)}ms note=reused_client",
    )

    text = await _generate_supervisor_text(
        client,
        user_prompt=user_prompt,
        session_id=session_id,
        turn_id=turn_id,
        t0=t0,
    )

    payload = _extract_json(text)
    decision = parse_supervisor_decision(payload)
    log_event(
        "SUP",
        "json_parsed",
        session_id=session_id,
        turn_id=turn_id,
        detail=(
            f"+{_ms_since(t0)}ms action={decision.action} "
            f"utterance_chars={len(decision.spoken_utterance)}"
        ),
    )
    return decision
