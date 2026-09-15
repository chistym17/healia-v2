/**
 * Offline mock helpers (not used by the live LiveKit consultation path).
 */
import {
  MOCK_DELAYS,
  MOCK_GREETING,
  MOCK_HEALIA_CLOSE,
  MOCK_HEALIA_FOLLOWUP,
  MOCK_USER_FOLLOWUP,
  MOCK_USER_TURN,
} from "@/v2/data/mockConsultation";
import type { TranscriptMessage, VoiceState } from "@/v2/types/consultation";

export type SessionMockCallbacks = {
  setVoiceState: (state: VoiceState) => void;
  appendMessage: (message: TranscriptMessage) => void;
};

let mockTurnIndex = 0;

const MOCK_SCRIPT: TranscriptMessage[] = [
  MOCK_USER_TURN,
  MOCK_HEALIA_FOLLOWUP,
  MOCK_USER_FOLLOWUP,
  MOCK_HEALIA_CLOSE,
];

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function createId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

async function playHealiaTurn(callbacks: SessionMockCallbacks) {
  const turn = MOCK_SCRIPT[mockTurnIndex];
  if (!turn || turn.role !== "healia") return;

  callbacks.setVoiceState("speaking");
  callbacks.appendMessage({ ...turn, id: createId("healia") });
  mockTurnIndex += 1;
  await delay(MOCK_DELAYS.speaking);
  callbacks.setVoiceState("ready");
}

export async function mockStartSession(
  callbacks: SessionMockCallbacks,
): Promise<void> {
  mockTurnIndex = 0;
  callbacks.setVoiceState("ready");
}

export async function mockSubmitVoiceTurn(
  callbacks: SessionMockCallbacks,
): Promise<void> {
  const userTurn = MOCK_SCRIPT[mockTurnIndex];
  if (!userTurn || userTurn.role !== "user") return;

  callbacks.setVoiceState("thinking");
  callbacks.appendMessage({ ...userTurn, id: createId("user") });
  mockTurnIndex += 1;
  await delay(MOCK_DELAYS.thinking);

  await playHealiaTurn(callbacks);
}

export async function mockSubmitTextTurn(
  text: string,
  callbacks: SessionMockCallbacks,
): Promise<void> {
  callbacks.setVoiceState("thinking");
  callbacks.appendMessage({
    id: createId("user"),
    role: "user",
    text: text.trim(),
  });

  if (MOCK_SCRIPT[mockTurnIndex]?.role === "user") {
    mockTurnIndex += 1;
  }

  await delay(MOCK_DELAYS.thinking);
  await playHealiaTurn(callbacks);
}

export function mockGetInitialGreeting(): TranscriptMessage {
  return MOCK_GREETING;
}

export function mockResetSessionMock() {
  mockTurnIndex = 0;
}

export function mockHasMoreTurns(): boolean {
  return mockTurnIndex < MOCK_SCRIPT.length;
}
