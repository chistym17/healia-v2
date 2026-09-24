"""Tunable LiveKit + Gemini Live (voice) + Groq text LLM settings.

Edit values here while testing. Agent code should only read from this module.

Env overrides (optional):
  RERANK_ENABLED=true|false  — turn BGE cross-encoder on/off (default true).
                               When false and mode is rerank, falls back to hybrid.
  SUPERVISOR_MODEL / GUIDANCE_MODEL — Groq model ids (default openai/gpt-oss-20b)
  GROQ_API_KEY — required for supervisor + guidance text LLM
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# --- Voice model (Gemini Realtime — keep for speak/listen) ---
MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"
VOICE = "Puck"
TEMPERATURE = 0.5
AGENT_NAME = "healia"

# --- Behavior ---
INSTRUCTIONS = """
You are Healia, a realtime voice assistant.

Keep every reply to 1-2 short sentences (under 20 words when possible).
The user speaks English, sometimes with a South Asian accent — listen to their intent, not exact wording.
Do not ask the same question twice if the user already answered.
Ask one question at a time.
Do not claim to provide a medical diagnosis.
This is currently a voice-system test.
""".strip()

GREETING_INSTRUCTIONS = (
    "Say hi in one short sentence and ask how you can help. Do not repeat the greeting."
)
ENABLE_GREETING = True

# --- Thinking (Gemini 2.5: thinking_budget; set 0 for lowest latency) ---
INCLUDE_THOUGHTS = False
THINKING_BUDGET = 0

# --- Turn detection ---
# "realtime_llm" = Gemini hears audio directly and decides when to reply (use this).
# "stt" = AssemblyAI decides turns — needs u3-rt-pro; broke comprehension on streaming-english.
TURN_DETECTION = "realtime_llm"
TURN_ENDPOINTING_MIN_DELAY_S = 0.0

# --- Gemini VAD ---
VAD_ENABLED = True
SILENCE_DURATION_MS = 900
PREFIX_PADDING_MS = 200
START_OF_SPEECH_SENSITIVITY = "HIGH"
END_OF_SPEECH_SENSITIVITY = "HIGH"

# --- Part 2: AssemblyAI STT (logging only; does not control replies) ---
STT_ENABLED = True
STT_MODEL = "universal-streaming-english"
# Wait after speech ends before committing the turn (gives user time to finish).
STT_SETTLE_MS = 1000
STT_LOG_INTERIM = False
# Only used when TURN_DETECTION == "stt".
STT_MIN_TURN_SILENCE_MS = 300
STT_MAX_TURN_SILENCE_MS = 1500
STT_VOICE_FOCUS = None

# --- Part 3: Supervisor (text LLM via Groq — not realtime voice) ---
SUPERVISOR_ENABLED = True
# log_only  = step 1: supervisor logs decisions; Gemini still free-chats
# controlled = step 2: Gemini speaks only supervisor spoken_utterance
SUPERVISOR_MODE = "controlled"
# Groq OpenAI GPT-OSS (override with SUPERVISOR_MODEL env)
SUPERVISOR_MODEL = (
    os.getenv("SUPERVISOR_MODEL") or "openai/gpt-oss-20b"
).strip()
SUPERVISOR_TEMPERATURE = 0.2
SUPERVISOR_MAX_FOLLOWUPS = 8
SUPERVISOR_TIMEOUT_SEC = float(os.getenv("SUPERVISOR_TIMEOUT_SEC") or "15")
LLM_FATAL_UTTERANCE = (
    "I'm having a technical problem and need to end this consultation. "
    "Please try again in a little while."
)

# --- Part 4: Mock assessment RAG (interface only) ---
ASSESSMENT_RAG_ENABLED = True

# --- Part 5: Knowledge RAG + spoken guidance (StatPearls corpus) ---
KNOWLEDGE_RAG_ENABLED = True
KNOWLEDGE_RAG_MODE = "rerank"  # faiss | bm25 | hybrid | rerank
KNOWLEDGE_RAG_TOP_K = 5
GUIDANCE_MODEL = (os.getenv("GUIDANCE_MODEL") or SUPERVISOR_MODEL).strip()
GUIDANCE_TEMPERATURE = 0.3
GUIDANCE_MAX_OUTPUT_TOKENS = 1024
GUIDANCE_TIMEOUT_SEC = float(os.getenv("GUIDANCE_TIMEOUT_SEC") or "20")


def _env_bool(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return default
    value = str(raw).strip().lower()
    if value in ("0", "false", "no", "off"):
        return False
    if value in ("1", "true", "yes", "on"):
        return True
    return default


# BGE cross-encoder (:8081). Set RERANK_ENABLED=false to skip without changing mode.
# Read via is_rerank_enabled() / effective_knowledge_rag_mode() so .env is honored at call time.


def is_rerank_enabled() -> bool:
    return _env_bool("RERANK_ENABLED", True)


# Snapshot for logging at import; prefer is_rerank_enabled() at runtime.
RERANK_ENABLED = is_rerank_enabled()


def effective_knowledge_rag_mode(mode: str | None = None) -> str:
    """Resolve retrieval mode; demote rerank → hybrid when RERANK_ENABLED=false."""
    resolved = (mode or KNOWLEDGE_RAG_MODE or "hybrid").lower().strip()
    if resolved in ("rerank", "hybrid_rerank") and not is_rerank_enabled():
        return "hybrid"
    return resolved


# --- Pipeline observability (logs + optional LiveKit data channel for UI) ---
PIPELINE_EVENTS_ENABLED = True
PIPELINE_EVENTS_LOG_JSON = True
PIPELINE_EVENTS_TO_ROOM = True
# Mirror RAG/guidance phases to FastAPI stdout (separate from voice agent logs).
PIPELINE_EVENTS_TO_API = _env_bool("PIPELINE_EVENTS_TO_API", True)
HEALIA_API_BASE_URL = (
    os.getenv("HEALIA_API_URL") or "http://127.0.0.1:8000"
).rstrip("/")
# Phases mirrored to FastAPI — not voice turn/speech/supervisor chatter.
PIPELINE_API_MIRROR_PHASES = frozenset(
    {
        "assessment_rag",
        "case_package",
        "knowledge_rag",
        "guidance",
    }
)

# Gemini voice instructions when SUPERVISOR_MODE == "controlled"
CONTROLLED_VOICE_INSTRUCTIONS = """
You are Healia's voice output only.

Rules:
- Never initiate conversation on your own.
- Never add diagnoses, treatments, doses, or medical facts.
- Only speak the content given to you in generate_reply instructions.
- Keep the same meaning; be natural but brief.
""".strip()
