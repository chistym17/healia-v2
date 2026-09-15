/**
 * Legacy mock session helpers retained for offline UI experiments.
 * Live consultations use LiveKit via LiveKitConsultationShell.
 */
export {
  mockGetInitialGreeting,
  mockResetSessionMock,
  mockStartSession,
  mockSubmitTextTurn,
  mockSubmitVoiceTurn,
  mockHasMoreTurns,
} from "@/v2/hooks/useConsultationSession.mock";
