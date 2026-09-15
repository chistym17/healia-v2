import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useNavigate } from "react-router-dom";
import { LIVE_PROCESSING_STEPS } from "@/v2/lib/pipeline";
import type {
  GuidanceResult,
  ProcessingStep,
  TranscriptMessage,
  VoiceState,
} from "@/v2/types/consultation";

type ConsultationContextValue = {
  voiceState: VoiceState;
  transcript: TranscriptMessage[];
  guidance: GuidanceResult | null;
  isListening: boolean;
  isProcessingTurn: boolean;
  sessionStarted: boolean;
  liveSessionActive: boolean;
  liveSessionKey: number;
  micEnabled: boolean;
  connectionError: string | null;
  processingSteps: ProcessingStep[];
  completedStepIds: string[];
  activeStepId: string | null;
  guidanceReady: boolean;
  startSession: () => void;
  setVoiceState: (state: VoiceState) => void;
  setMicEnabled: (enabled: boolean) => void;
  toggleListening: () => void;
  appendMessage: (message: TranscriptMessage) => void;
  markProcessingStep: (stepId: string, status: "active" | "completed") => void;
  setGuidanceResult: (result: GuidanceResult) => void;
  goToProcessing: () => void;
  goToResults: () => void;
  endConsultation: () => void;
  endLiveSession: () => void;
  stopAgent: () => void;
  resetConsultation: () => void;
  setConnectionError: (message: string | null) => void;
  sendTextMessage: (text: string) => Promise<void>;
  registerTextSender: (sender: ((text: string) => Promise<void>) | null) => void;
  registerMicToggle: (toggle: ((enabled: boolean) => Promise<void>) | null) => void;
};

const ConsultationContext = createContext<ConsultationContextValue | null>(
  null,
);

function createId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

export function ConsultationProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const [voiceState, setVoiceState] = useState<VoiceState>("ready");
  const [transcript, setTranscript] = useState<TranscriptMessage[]>([]);
  const [guidance, setGuidance] = useState<GuidanceResult | null>(null);
  const [sessionStarted, setSessionStarted] = useState(false);
  const [liveSessionActive, setLiveSessionActive] = useState(false);
  const [micEnabled, setMicEnabled] = useState(true);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [completedStepIds, setCompletedStepIds] = useState<string[]>([]);
  const [activeStepId, setActiveStepId] = useState<string | null>(null);
  const [guidanceReady, setGuidanceReady] = useState(false);
  const [liveSessionKey, setLiveSessionKey] = useState(0);
  const textSenderRef = useRef<((text: string) => Promise<void>) | null>(null);
  const micToggleRef = useRef<((enabled: boolean) => Promise<void>) | null>(
    null,
  );
  const seenTranscriptKeys = useRef(new Set<string>());

  const isListening = voiceState === "listening" && micEnabled;
  const isProcessingTurn =
    voiceState === "thinking" || voiceState === "speaking";

  const appendMessage = useCallback((message: TranscriptMessage) => {
    const key = `${message.role}:${message.text}`;
    if (seenTranscriptKeys.current.has(key)) return;
    seenTranscriptKeys.current.add(key);
    setTranscript((prev) => [...prev, message]);
  }, []);

  const resetConsultation = useCallback(() => {
    seenTranscriptKeys.current.clear();
    textSenderRef.current = null;
    micToggleRef.current = null;
    setVoiceState("ready");
    setTranscript([]);
    setGuidance(null);
    setSessionStarted(false);
    setLiveSessionActive(false);
    setMicEnabled(true);
    setConnectionError(null);
    setCompletedStepIds([]);
    setActiveStepId(null);
    setGuidanceReady(false);
  }, []);

  const startSession = useCallback(() => {
    seenTranscriptKeys.current.clear();
    setGuidance(null);
    setTranscript([]);
    setConnectionError(null);
    setCompletedStepIds([]);
    setActiveStepId(null);
    setGuidanceReady(false);
    setMicEnabled(true);
    setVoiceState("ready");
    setSessionStarted(true);
    setLiveSessionKey((k) => k + 1);
    setLiveSessionActive(true);
  }, []);

  const endLiveSession = useCallback(() => {
    setLiveSessionActive(false);
    setSessionStarted(false);
    setVoiceState("ready");
  }, []);

  const stopAgent = useCallback(() => {
    setLiveSessionActive(false);
    setSessionStarted(false);
    setVoiceState("ready");
    setConnectionError(null);
    setMicEnabled(true);
  }, []);

  const markProcessingStep = useCallback(
    (stepId: string, status: "active" | "completed") => {
      if (status === "active") {
        setActiveStepId(stepId);
        return;
      }
      setCompletedStepIds((prev) =>
        prev.includes(stepId) ? prev : [...prev, stepId],
      );
      const order = LIVE_PROCESSING_STEPS.map((s) => s.id);
      const next = order[order.indexOf(stepId) + 1];
      setActiveStepId(next ?? null);
    },
    [],
  );

  const setGuidanceResult = useCallback((result: GuidanceResult) => {
    setGuidance(result);
    setGuidanceReady(true);
    setCompletedStepIds(LIVE_PROCESSING_STEPS.map((s) => s.id));
    setActiveStepId(null);
  }, []);

  const goToProcessing = useCallback(() => {
    navigate("/v2/consultation/processing");
  }, [navigate]);

  const goToResults = useCallback(() => {
    navigate("/v2/consultation/results");
  }, [navigate]);

  const endConsultation = useCallback(() => {
    // Manual end — if guidance already ready, go to results; else processing.
    if (guidanceReady) {
      navigate("/v2/consultation/results");
      return;
    }
    markProcessingStep("symptoms", "active");
    navigate("/v2/consultation/processing");
  }, [guidanceReady, markProcessingStep, navigate]);

  const registerTextSender = useCallback(
    (sender: ((text: string) => Promise<void>) | null) => {
      textSenderRef.current = sender;
    },
    [],
  );

  const registerMicToggle = useCallback(
    (toggle: ((enabled: boolean) => Promise<void>) | null) => {
      micToggleRef.current = toggle;
    },
    [],
  );

  const toggleListening = useCallback(() => {
    const next = !micEnabled;
    setMicEnabled(next);
    void micToggleRef.current?.(next);
  }, [micEnabled]);

  const sendTextMessage = useCallback(async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || !textSenderRef.current) return;
    appendMessage({
      id: createId("user"),
      role: "user",
      text: trimmed,
    });
    await textSenderRef.current(trimmed);
  }, [appendMessage]);

  const value = useMemo<ConsultationContextValue>(
    () => ({
      voiceState,
      transcript,
      guidance,
      isListening,
      isProcessingTurn,
      sessionStarted,
      liveSessionActive,
      liveSessionKey,
      micEnabled,
      connectionError,
      processingSteps: LIVE_PROCESSING_STEPS,
      completedStepIds,
      activeStepId,
      guidanceReady,
      startSession,
      setVoiceState,
      setMicEnabled,
      toggleListening,
      appendMessage,
      markProcessingStep,
      setGuidanceResult,
      goToProcessing,
      goToResults,
      endConsultation,
      endLiveSession,
      stopAgent,
      resetConsultation,
      setConnectionError,
      sendTextMessage,
      registerTextSender,
      registerMicToggle,
    }),
    [
      voiceState,
      transcript,
      guidance,
      isListening,
      isProcessingTurn,
      sessionStarted,
      liveSessionActive,
      liveSessionKey,
      micEnabled,
      connectionError,
      completedStepIds,
      activeStepId,
      guidanceReady,
      startSession,
      toggleListening,
      appendMessage,
      markProcessingStep,
      setGuidanceResult,
      goToProcessing,
      goToResults,
      endConsultation,
      endLiveSession,
      stopAgent,
      resetConsultation,
      sendTextMessage,
      registerTextSender,
      registerMicToggle,
    ],
  );

  return (
    <ConsultationContext.Provider value={value}>
      {children}
    </ConsultationContext.Provider>
  );
}

export function useConsultation() {
  const ctx = useContext(ConsultationContext);
  if (!ctx) {
    throw new Error("useConsultation must be used within ConsultationProvider");
  }
  return ctx;
}
