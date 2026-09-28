import type { AgentState } from "@livekit/components-react";
import type { VoiceState } from "@/v2/types/consultation";

/** Active turn states — means the agent has joined and the consult can proceed. */
export function isAgentTurnState(state: AgentState): boolean {
  return (
    state === "listening" || state === "thinking" || state === "speaking"
  );
}

/**
 * Map LiveKit agent lifecycle → Healia voice UI.
 * `agentHasJoined` is true once we've seen listening/thinking/speaking;
 * until then, idle/buffering stay in "connecting" so we never prompt "speak now" early.
 */
export function mapAgentStateToVoiceState(
  state: AgentState,
  agentHasJoined: boolean,
): VoiceState {
  switch (state) {
    case "listening":
      return "listening";
    case "thinking":
      return "thinking";
    case "speaking":
      return "speaking";
    case "failed":
    case "disconnected":
      return "error";
    case "connecting":
    case "initializing":
    case "pre-connect-buffering":
      return "connecting";
    case "idle":
      // Cold start: agent may sit in idle before the greeting.
      // After join: quiet pause between turns → ready.
      return agentHasJoined ? "ready" : "connecting";
    default:
      return agentHasJoined ? "ready" : "connecting";
  }
}
