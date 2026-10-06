from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any

from livekit_agent import config
from livekit_agent.events import log_event
from livekit_agent.llm_client import groq_json_completion

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

Core rules:
- Output JSON only, matching the schema exactly.
- One action per turn.
- spoken_utterance: short (1-2 sentences), one question max for ask_followup.
- Do not diagnose, prescribe, or give treatment plans.
- English only.

Complaint & corrections (critical):
- Never invent a chief complaint from greetings, silence, or assessment hints alone.
- Set state_updates.chief_complaint only when the patient clearly states a symptom/problem.
- If the patient denies or corrects a complaint (e.g. "I'm not having hiccups",
  "that's wrong", "what are you talking about"), you MUST:
  1) put the wrong label in state_updates.deny_complaints,
  2) set state_updates.clear_chief_complaint=true when the current chief_complaint is wrong,
  3) apologize briefly and ask what problem they DO want help with (ask_followup or acknowledge).
- Never ask again about anything in consultation_state.denied_complaints.
- Prefer state_updates.corrections when the patient fixes earlier facts.

Follow-up quality:
- The next question MUST respond to the patient's latest turn, not the next list item.
- For ask_followup, set followup_topic to a short snake_case key (e.g. headache_location).
- Do not ask about topics already in asked_topics unless correcting a fact.
- Prefer acknowledge when the patient only greets or gives no new medical info.
- Ask for the next missing useful detail about THEIR real complaint first
  (where, when started, severity, change, key associated signs) before generic checklist items.
- Do NOT rotate the same generic quartet every consult (medications / past history /
  saw a doctor / what triggered it) unless complaint-specific details are already covered.
- Use build_final_query when you have enough for a coherent final_query_draft.
- Use escalate for emergency/red-flag language (chest pain, can't breathe, suicide, etc.).

Assessment hints (optional only):
- If assessment_evidence.suggested_questions is present: treat each item as a THEME only
  (theme / question_type / medical_topic). Never copy the hint question verbatim.
- Ignore any hint that conflicts with the patient's latest answer or denied_complaints.
- If assessment_evidence was skipped/empty, decide from patient_turn + consultation_state alone.

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
    "clear_chief_complaint": false,
    "deny_complaints": ["optional list of rejected complaint labels"],
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
        detail=f"+0ms model={config.SUPERVISOR_MODEL} provider=groq",
    )
    try:
        log_event(
            "SUP",
            "client_ready",
            session_id=session_id,
            turn_id="warmup",
            detail=f"+{_ms_since(t0)}ms note=groq",
        )
        await groq_json_completion(
            system=_SYSTEM_PROMPT,
            user='{"patient_turn":"hi","consultation_state":{"phase":"gathering","facts":{},"asked_topics":[]}}',
            model=config.SUPERVISOR_MODEL,
            temperature=config.SUPERVISOR_TEMPERATURE,
            max_tokens=64,
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
    *,
    user_prompt: str,
    session_id: str,
    turn_id: str,
    t0: float,
) -> str:
    """Call Groq GPT-OSS for supervisor JSON."""
    log_event(
        "SUP",
        "request_sent",
        session_id=session_id,
        turn_id=turn_id,
        detail=f"+{_ms_since(t0)}ms model={config.SUPERVISOR_MODEL} mode=groq",
    )
    text = await groq_json_completion(
        system=_SYSTEM_PROMPT,
        user=user_prompt,
        model=config.SUPERVISOR_MODEL,
        temperature=config.SUPERVISOR_TEMPERATURE,
    )
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
    """Part 3A: Groq text LLM; staged timing logs."""
    t0 = time.monotonic()
    log_event(
        "SUP",
        "request_start",
        session_id=session_id,
        turn_id=turn_id,
        detail=f"+0ms model={config.SUPERVISOR_MODEL} provider=groq",
    )

    payload_in: dict[str, Any] = {
        "patient_turn": patient_turn,
        "consultation_state": state,
    }
    if assessment_evidence is not None:
        payload_in["assessment_evidence"] = assessment_evidence

    user_prompt = json.dumps(payload_in, ensure_ascii=False)

    log_event(
        "SUP",
        "client_ready",
        session_id=session_id,
        turn_id=turn_id,
        detail=f"+{_ms_since(t0)}ms note=groq",
    )

    text = await _generate_supervisor_text(
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
