"""Healia LiveKit voice agent — Gemini realtime audio."""

import logging

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, JobContext
from livekit.plugins import google

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("healia-agent")


class HealiaAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
            You are Healia, a realtime voice assistant.

            Speak naturally and keep your responses concise.
            Ask one question at a time.
            This is currently a voice-system test.
            Do not claim to provide a medical diagnosis.
            """
        )


server = AgentServer()


@server.rtc_session(agent_name="healia")
async def healia_session(ctx: JobContext) -> None:
    logger.info("Starting Healia session in room: %s", ctx.room.name)

    session = AgentSession(
        llm=google.realtime.RealtimeModel(
            model="gemini-3.1-flash-live-preview",
            voice="Puck",
        )
    )

    await session.start(
        room=ctx.room,
        agent=HealiaAgent(),
    )

    await session.generate_reply(
        instructions="Greet the user briefly and ask how you can help."
    )


if __name__ == "__main__":
    agents.cli.run_app(server)
