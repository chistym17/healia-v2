import { API_URL } from "@/v2/lib/api";
import { getAccessToken } from "@/v2/lib/authStorage";
import type {
  CompleteSessionPayload,
  SessionRecord,
  SessionSummary,
  StoredSessionResults,
  StoredTranscriptMessage,
  SessionStatus,
} from "@/v2/types/session";

async function parseError(res: Response): Promise<string> {
  try {
    const data = (await res.json()) as { detail?: string };
    if (typeof data.detail === "string") return data.detail;
  } catch {
    /* ignore */
  }
  return res.statusText || "Request failed";
}

async function authFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getAccessToken();
  if (!token) throw new Error("Not signed in");

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
  });

  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<T>;
}

export async function createSession(input?: {
  livekit_room_name?: string;
  title?: string;
  status?: SessionStatus;
}): Promise<SessionRecord> {
  const data = await authFetch<{ session: SessionRecord }>("/api/sessions", {
    method: "POST",
    body: JSON.stringify({
      status: input?.status ?? "started",
      title: input?.title,
      livekit_room_name: input?.livekit_room_name,
    }),
  });
  return data.session;
}

export async function listSessions(limit = 50): Promise<SessionSummary[]> {
  const data = await authFetch<{ sessions: SessionSummary[] }>(
    `/api/sessions?limit=${limit}`,
  );
  return data.sessions;
}

export async function getSession(
  sessionId: string,
): Promise<{ session: SessionRecord; results: StoredSessionResults | null }> {
  return authFetch(`/api/sessions/${sessionId}`);
}

export async function updateSession(
  sessionId: string,
  body: {
    status?: SessionStatus;
    title?: string;
    transcript?: StoredTranscriptMessage[];
    livekit_room_name?: string;
  },
): Promise<SessionRecord> {
  const data = await authFetch<{ session: SessionRecord }>(
    `/api/sessions/${sessionId}`,
    {
      method: "PATCH",
      body: JSON.stringify(body),
    },
  );
  return data.session;
}

export async function completeSession(
  sessionId: string,
  body: CompleteSessionPayload,
): Promise<{ session: SessionRecord; results: StoredSessionResults }> {
  return authFetch(`/api/sessions/${sessionId}/complete`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function transcriptToStored(
  messages: Array<{ role: "user" | "healia"; text: string }>,
): StoredTranscriptMessage[] {
  return messages.map((m) => ({
    role: m.role,
    text: m.text,
    ts: new Date().toISOString(),
  }));
}

export function titleFromTranscript(
  messages: Array<{ role: string; text: string }>,
): string {
  const firstUser = messages.find((m) => m.role === "user" && m.text.trim());
  if (!firstUser) return "Health consultation";
  const text = firstUser.text.trim();
  return text.length > 72 ? `${text.slice(0, 69)}…` : text;
}
