import type { TranscriptMessage } from "@/v2/types/consultation";

/** Minimum non-whitespace length to count as a real patient utterance. */
const MIN_USER_CHARS = 3;

/**
 * True when the patient has shared enough for guidance to be worth running.
 * Greeting-only / empty sessions fail this check.
 */
export function hasEnoughPatientInfo(
  transcript: TranscriptMessage[],
): boolean {
  return transcript.some(
    (m) =>
      m.role === "user" && m.text.trim().replace(/\s+/g, " ").length >= MIN_USER_CHARS,
  );
}
