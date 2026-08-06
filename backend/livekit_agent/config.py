"""Tunable LiveKit + Gemini Live settings.

Edit values here while testing. Agent code should only read from this module.
"""

from __future__ import annotations

# --- Model ---
MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"
VOICE = "Puck"
TEMPERATURE = 0.7
AGENT_NAME = "healia"

# --- Behavior ---
# Keep instructions in ONE place (RealtimeModel). Agent class stays thin.
INSTRUCTIONS = """
You are Healia, a realtime voice assistant.

Speak naturally and keep responses concise.
Ask one question at a time.
Do not repeat yourself unless the user asks you to.
Do not claim to provide a medical diagnosis.
This is currently a voice-system test.
""".strip()

GREETING_INSTRUCTIONS = (
    "Greet the user briefly and ask how you can help today. Do not repeat the greeting."
)
ENABLE_GREETING = True

# --- Thinking (lower latency when thoughts are off) ---
INCLUDE_THOUGHTS = False

# --- Gemini built-in VAD / turn detection ---
# Docs suggest ~500–800ms silence for a balance of latency vs mid-sentence cuts.
# Tweak these while testing response delay and double-answers.
VAD_ENABLED = True
SILENCE_DURATION_MS = 600
PREFIX_PADDING_MS = 20
# "LOW" | "HIGH" — mapped in agent.py to google.genai types
START_OF_SPEECH_SENSITIVITY = "LOW"
END_OF_SPEECH_SENSITIVITY = "LOW"
