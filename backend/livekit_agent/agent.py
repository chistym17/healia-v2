"""Healia LiveKit voice agent — Gemini realtime audio."""

import logging

from dotenv import load_dotenv
from google.genai import types
from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, JobContext
from livekit.plugins import google

from livekit_agent import config

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("healia-agent")


def _speech_sensitivity(kind: str, value: str):
    """Map config strings to google.genai sensitivity enums."""
    value = (value or "LOW").upper()
    if kind == "start":
        return (
            types.StartSensitivity.START_SENSITIVITY_HIGH
            if value == "HIGH"
            else types.StartSensitivity.START_SENSITIVITY_LOW
        )
    return (
        types.EndSensitivity.END_SENSITIVITY_HIGH
        if value == "HIGH"
        else types.EndSensitivity.END_SENSITIVITY_LOW
    )


def build_realtime_model() -> google.realtime.RealtimeModel:
    kwargs: dict = {
        "model": config.MODEL,
        "voice": config.VOICE,
        "temperature": config.TEMPERATURE,
        "instructions": config.INSTRUCTIONS,
        "thinking_config": types.ThinkingConfig(
            include_thoughts=config.INCLUDE_THOUGHTS,
        ),
    }

    if config.VAD_ENABLED:
        kwargs["realtime_input_config"] = types.RealtimeInputConfig(
            automatic_activity_detection=types.AutomaticActivityDetection(
                disabled=False,
                start_of_speech_sensitivity=_speech_sensitivity(
                    "start", config.START_OF_SPEECH_SENSITIVITY
                ),
                end_of_speech_sensitivity=_speech_sensitivity(
                    "end", config.END_OF_SPEECH_SENSITIVITY
                ),
                prefix_padding_ms=config.PREFIX_PADDING_MS,
                silence_duration_ms=config.SILENCE_DURATION_MS,
            )
        )

    return google.realtime.RealtimeModel(**kwargs)


class HealiaAgent(Agent):
    def __init__(self) -> None:
        # Instructions live on RealtimeModel via config — keep Agent minimal.
        super().__init__(instructions=config.INSTRUCTIONS)


server = AgentServer()


@server.rtc_session(agent_name=config.AGENT_NAME)
async def healia_session(ctx: JobContext) -> None:
    logger.info(
        "Starting Healia session room=%s model=%s silence_ms=%s",
        ctx.room.name,
        config.MODEL,
        config.SILENCE_DURATION_MS,
    )

    await ctx.connect()

    session = AgentSession(llm=build_realtime_model())

    await session.start(
        room=ctx.room,
        agent=HealiaAgent(),
    )

    if config.ENABLE_GREETING:
        await session.generate_reply(instructions=config.GREETING_INSTRUCTIONS)


if __name__ == "__main__":
    agents.cli.run_app(server)
