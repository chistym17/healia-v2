export const API_URL =
  import.meta.env.VITE_API_URL ||
  import.meta.env.VITE_SERVER_URL ||
  "http://localhost:8000";

export const LIVEKIT_TOKEN_URL = `${API_URL}/api/livekit/token`;

export const HEALIA_AGENT_NAME = "healia";

export const PIPELINE_TOPIC = "healia.pipeline";

/** Client → agent control messages (e.g. user ended session). */
export const CONTROL_TOPIC = "healia.control";
