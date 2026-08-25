from __future__ import annotations

from livekit.agents import AgentSession

from livekit_agent.supervisor import SupervisorDecision


def build_speech_instructions(decision: SupervisorDecision) -> str:
    text = decision.spoken_utterance.strip()
    if decision.allow_light_paraphrase:
        return (
            "Say the following to the patient. You may lightly rephrase for natural speech "
            "but keep the same meaning and do not add any medical advice:\n\n"
            f"{text}"
        )
    return (
        "Say exactly the following to the patient. Do not add or omit information:\n\n"
        f"{text}"
    )


async def speak_decision(session: AgentSession, decision: SupervisorDecision) -> None:
    if not decision.spoken_utterance.strip():
        return
    await session.generate_reply(
        instructions=build_speech_instructions(decision),
        tool_choice="none",
    )
