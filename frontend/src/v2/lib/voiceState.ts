import type { AgentState } from "@livekit/components-react";
import type { VoiceState } from "@/v2/types/consultation";

export function mapAgentStateToVoiceState(state: AgentState): VoiceState {
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
    case "idle":
    default:
      return "ready";
  }
}
