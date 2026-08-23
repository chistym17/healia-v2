from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

from google import genai
from google.genai import types

from livekit_agent import config

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
- For ask_followup, set followup_topic to a short snake_case key (e.g. weight_loss_goal).
- Do not ask about topics already in asked_topics unless correcting a fact.
- Prefer acknowledge when the patient only greets or gives no new medical info.
- Use build_final_query when you have enough for a coherent final_query_draft.
- Use escalate for emergency/red-flag language (chest pain, can't breathe, suicide, etc.).
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


async def run_supervisor(
    *,
    patient_turn: str,
    state: dict[str, Any],
) -> SupervisorDecision:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set")

    user_prompt = json.dumps(
        {
            "patient_turn": patient_turn,
            "consultation_state": state,
        },
        ensure_ascii=False,
    )

    client = genai.Client(api_key=api_key)
    response = await client.aio.models.generate_content(
        model=config.SUPERVISOR_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            temperature=config.SUPERVISOR_TEMPERATURE,
            response_mime_type="application/json",
        ),
    )

    text = (response.text or "").strip()
    payload = _extract_json(text)
    return parse_supervisor_decision(payload)
