"""Tunable LiveKit + Gemini Live settings.

Edit values here while testing. Agent code should only read from this module.
"""

from __future__ import annotations

# --- Model ---
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
SILENCE_DURATION_MS = 500
PREFIX_PADDING_MS = 200
START_OF_SPEECH_SENSITIVITY = "HIGH"
END_OF_SPEECH_SENSITIVITY = "HIGH"

# --- Part 2: AssemblyAI STT (logging only; does not control replies) ---
STT_ENABLED = True
STT_MODEL = "universal-streaming-english"
STT_SETTLE_MS = 400
STT_LOG_INTERIM = False
# Only used when TURN_DETECTION == "stt".
STT_MIN_TURN_SILENCE_MS = 100
STT_MAX_TURN_SILENCE_MS = 900
STT_VOICE_FOCUS = None

# --- Part 3: Supervisor ---
SUPERVISOR_ENABLED = True
# log_only  = step 1: supervisor logs decisions; Gemini still free-chats
# controlled = step 2: Gemini speaks only supervisor spoken_utterance
SUPERVISOR_MODE = "controlled"
SUPERVISOR_MODEL = "gemini-2.0-flash"
SUPERVISOR_TEMPERATURE = 0.2
SUPERVISOR_MAX_FOLLOWUPS = 8

# Gemini voice instructions when SUPERVISOR_MODE == "controlled"
CONTROLLED_VOICE_INSTRUCTIONS = """
You are Healia's voice output only.

Rules:
- Never initiate conversation on your own.
- Never add diagnoses, treatments, doses, or medical facts.
- Only speak the content given to you in generate_reply instructions.
- Keep the same meaning; be natural but brief.
""".strip()
