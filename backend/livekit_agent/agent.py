import uuid

from dotenv import load_dotenv
from google.genai import types
from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, JobContext
from livekit.plugins import google

from livekit_agent import config
from livekit_agent.events import log_event

load_dotenv()


def _speech_sensitivity(kind: str, value: str):
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
        super().__init__(instructions=config.INSTRUCTIONS)


def _attach_voice_logs(session: AgentSession, session_id: str) -> None:
    @session.on("agent_state_changed")
    def _on_agent_state(ev) -> None:
        log_event(
            "VOICE",
            "agent_state",
            session_id=session_id,
            detail=f"{ev.old_state}->{ev.new_state}",
        )

    @session.on("user_state_changed")
    def _on_user_state(ev) -> None:
        log_event(
            "VOICE",
            "user_state",
            session_id=session_id,
            detail=f"{ev.old_state}->{ev.new_state}",
        )

    @session.on("speech_created")
    def _on_speech_created(ev) -> None:
        source = getattr(ev, "source", None) or getattr(ev, "user_initiated", "unknown")
        log_event(
            "VOICE",
            "speech_created",
            session_id=session_id,
            detail=f"source={source}",
        )

    @session.on("error")
    def _on_error(ev) -> None:
        log_event(
            "VOICE",
            "error",
            session_id=session_id,
            detail=str(getattr(ev, "error", ev)),
        )

    @session.on("close")
    def _on_close(ev) -> None:
        reason = getattr(ev, "reason", "")
        log_event(
            "VOICE",
            "session_closed",
            session_id=session_id,
            detail=f"reason={reason}",
        )


server = AgentServer()


@server.rtc_session(agent_name=config.AGENT_NAME)
async def healia_session(ctx: JobContext) -> None:
    session_id = f"sess_{uuid.uuid4().hex[:8]}"
    room_name = ctx.room.name

    log_event(
        "VOICE",
        "session_start",
        session_id=session_id,
        detail=f"room={room_name} model={config.MODEL}",
    )

    await ctx.connect()
    log_event("VOICE", "room_connected", session_id=session_id, detail=f"room={room_name}")

    session = AgentSession(llm=build_realtime_model())
    _attach_voice_logs(session, session_id)

    await session.start(room=ctx.room, agent=HealiaAgent())
    log_event(
        "VOICE",
        "agent_ready",
        session_id=session_id,
        detail="reply_path=gemini_auto",
    )

    # Part 1: only explicit reply initiation is the optional greeting.
    # After that, Gemini Live answers user audio by itself (one auto path).
    if config.ENABLE_GREETING:
        log_event(
            "VOICE",
            "greeting_requested",
            session_id=session_id,
            detail="via=generate_reply",
        )
        await session.generate_reply(instructions=config.GREETING_INSTRUCTIONS)
        log_event("VOICE", "greeting_done", session_id=session_id)


if __name__ == "__main__":
    agents.cli.run_app(server)
