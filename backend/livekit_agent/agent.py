import time
import uuid

from dotenv import load_dotenv
from google.genai import types
from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, JobContext

try:
    from livekit.agents import TurnHandlingOptions
except ImportError:  # older livekit-agents 1.6.x
    TurnHandlingOptions = None  # type: ignore[misc, assignment]
from livekit.plugins import assemblyai, google

from livekit_agent import config
from livekit_agent.events import log_event, start_session_log
from livekit_agent.turns import TurnAssembler

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


def _uses_stt_turn_detection() -> bool:
    return config.STT_ENABLED and config.TURN_DETECTION == "stt"


def build_realtime_model() -> google.realtime.RealtimeModel:
    kwargs: dict = {
        "model": config.MODEL,
        "voice": config.VOICE,
        "temperature": config.TEMPERATURE,
        "instructions": config.INSTRUCTIONS,
        "thinking_config": types.ThinkingConfig(
            include_thoughts=config.INCLUDE_THOUGHTS,
            thinking_budget=config.THINKING_BUDGET,
        ),
    }

    if _uses_stt_turn_detection():
        # Let LiveKit + AssemblyAI own turn boundaries; avoid dual VAD with Gemini.
        kwargs["realtime_input_config"] = types.RealtimeInputConfig(
            automatic_activity_detection=types.AutomaticActivityDetection(
                disabled=True,
            )
        )
    elif config.VAD_ENABLED:
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


_VOICE_FOCUS_MODELS = frozenset(
    {
        "u3-rt-pro",
        "u3-rt-pro-beta-1",
        "universal-3-5-pro",
    }
)


def build_stt():
    if not config.STT_ENABLED:
        return None

    kwargs: dict = {"model": config.STT_MODEL}
    if _uses_stt_turn_detection():
        if config.STT_MIN_TURN_SILENCE_MS is not None:
            kwargs["min_turn_silence"] = config.STT_MIN_TURN_SILENCE_MS
        if config.STT_MAX_TURN_SILENCE_MS is not None:
            kwargs["max_turn_silence"] = config.STT_MAX_TURN_SILENCE_MS
        if config.STT_VOICE_FOCUS and config.STT_MODEL in _VOICE_FOCUS_MODELS:
            kwargs["voice_focus"] = config.STT_VOICE_FOCUS
    return assemblyai.STT(**kwargs)


def build_turn_handling() -> dict | object | None:
    if not _uses_stt_turn_detection():
        return None
    if TurnHandlingOptions is not None:
        return TurnHandlingOptions(
            turn_detection="stt",
            endpointing={"min_delay": config.TURN_ENDPOINTING_MIN_DELAY_S},
        )
    return None


def apply_turn_handling(session_kwargs: dict) -> None:
    turn_handling = build_turn_handling()
    if turn_handling is not None:
        session_kwargs["turn_handling"] = turn_handling
        return
    if _uses_stt_turn_detection():
        session_kwargs["turn_detection"] = "stt"
        session_kwargs["min_endpointing_delay"] = config.TURN_ENDPOINTING_MIN_DELAY_S


class HealiaAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=config.INSTRUCTIONS)


def _attach_session_logs(
    session: AgentSession,
    session_id: str,
    turns: TurnAssembler | None,
) -> None:
    user_speech_started_at: float | None = None

    @session.on("agent_state_changed")
    def _on_agent_state(ev) -> None:
        nonlocal user_speech_started_at
        detail = f"{ev.old_state}->{ev.new_state}"
        if (
            ev.new_state == "speaking"
            and user_speech_started_at is not None
            and ev.old_state == "listening"
        ):
            latency_ms = int((time.monotonic() - user_speech_started_at) * 1000)
            detail = f"{detail} reply_latency_ms={latency_ms}"
            user_speech_started_at = None
        log_event(
            "VOICE",
            "agent_state",
            session_id=session_id,
            detail=detail,
        )

    @session.on("user_state_changed")
    def _on_user_state(ev) -> None:
        nonlocal user_speech_started_at
        log_event(
            "VOICE",
            "user_state",
            session_id=session_id,
            detail=f"{ev.old_state}->{ev.new_state}",
        )
        if ev.new_state == "speaking":
            user_speech_started_at = time.monotonic()
        if turns is None:
            return
        if ev.new_state == "speaking":
            turns.on_user_speaking()
        elif ev.old_state == "speaking" and ev.new_state in ("listening", "away"):
            turns.on_user_stopped()

    @session.on("user_input_transcribed")
    def _on_user_transcript(ev) -> None:
        if turns is None:
            return
        if not ev.is_final and not config.STT_LOG_INTERIM:
            return
        turns.on_transcript(ev.transcript, ev.is_final)

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
    log_path = start_session_log(session_id, room=room_name, model=config.MODEL)

    log_event(
        "VOICE",
        "session_start",
        session_id=session_id,
        detail=f"room={room_name} model={config.MODEL} log={log_path.name}",
    )

    await ctx.connect()
    log_event("VOICE", "room_connected", session_id=session_id, detail=f"room={room_name}")

    stt = build_stt()
    turns = TurnAssembler(session_id, settle_ms=config.STT_SETTLE_MS) if stt else None

    reply_path = "stt_turn_detection" if _uses_stt_turn_detection() else "gemini_auto"
    session_kwargs: dict = {"llm": build_realtime_model()}
    apply_turn_handling(session_kwargs)

    if stt is not None:
        session_kwargs["stt"] = stt
        log_event(
            "STT",
            "enabled",
            session_id=session_id,
            detail=f"model={config.STT_MODEL} mode=logging_only settle_ms={config.STT_SETTLE_MS}",
        )

    session = AgentSession(**session_kwargs)
    _attach_session_logs(session, session_id, turns)

    await session.start(room=ctx.room, agent=HealiaAgent())
    log_event(
        "VOICE",
        "agent_ready",
        session_id=session_id,
        detail=f"reply_path={reply_path}",
    )

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
