import { useEffect, useMemo, useRef } from "react";
import type { ReactNode } from "react";
import {
  RoomAudioRenderer,
  SessionProvider,
  StartAudio,
  useChat,
  useDataChannel,
  useSession,
  useVoiceAssistant,
} from "@livekit/components-react";
import { Room, TokenSource } from "livekit-client";
import { useConsultation } from "@/v2/context/ConsultationContext";
import {
  HEALIA_AGENT_NAME,
  LIVEKIT_TOKEN_URL,
  PIPELINE_TOPIC,
} from "@/v2/lib/api";
import { mapBackendGuidanceToResult } from "@/v2/lib/guidanceMapper";
import {
  isGuidanceReadyEvent,
  isProcessingStartEvent,
  isSpeechCompleteEvent,
  parsePipelinePayload,
  stepIdForPipelinePhase,
  type PipelineEvent,
} from "@/v2/lib/pipeline";
import { mapAgentStateToVoiceState } from "@/v2/lib/voiceState";

/** Max wait after guidance before leaving even if speech.completed never arrives. */
const SPEECH_FALLBACK_MS = 20_000;

function createId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

/**
 * Bridges LiveKit agent state + pipeline data channel into ConsultationContext.
 * Must render inside SessionProvider.
 */
function LiveKitBridge({ room }: { room: Room }) {
  const {
    setVoiceState,
    appendMessage,
    markProcessingStep,
    setGuidanceResult,
    goToProcessing,
    goToResults,
    setConnectionError,
    registerTextSender,
    registerMicToggle,
    setMicEnabled,
    micEnabled,
    endLiveSession,
  } = useConsultation();

  const { state } = useVoiceAssistant();
  const { send: sendChat } = useChat();
  const navigatedToProcessing = useRef(false);
  const guidanceStored = useRef(false);
  const finishedFlow = useRef(false);
  const speechFallbackTimer = useRef<number | null>(null);

  const finishAndShowResults = () => {
    if (finishedFlow.current) return;
    finishedFlow.current = true;
    if (speechFallbackTimer.current != null) {
      window.clearTimeout(speechFallbackTimer.current);
      speechFallbackTimer.current = null;
    }
    goToResults();
    // Brief delay so Results can mount before room teardown.
    window.setTimeout(() => {
      endLiveSession();
    }, 500);
  };

  useEffect(() => {
    setVoiceState(mapAgentStateToVoiceState(state));
    if (state === "failed") {
      setConnectionError(
        "We couldn't connect to Healia. Check that the API and voice agent are running, then try again.",
      );
    }
  }, [setConnectionError, setVoiceState, state]);

  useEffect(() => {
    registerMicToggle(async (enabled: boolean) => {
      try {
        await room.localParticipant.setMicrophoneEnabled(enabled);
      } catch (err) {
        console.error("Mic toggle failed:", err);
        setConnectionError(
          "Microphone access failed. Please allow microphone permission and try again.",
        );
      }
    });
    return () => registerMicToggle(null);
  }, [registerMicToggle, room, setConnectionError]);

  useEffect(() => {
    void room.localParticipant.setMicrophoneEnabled(micEnabled).catch(() => {
      /* ignore until connected */
    });
  }, [micEnabled, room]);

  useEffect(() => {
    registerTextSender(async (text: string) => {
      await sendChat(text);
    });
    return () => registerTextSender(null);
  }, [registerTextSender, sendChat]);

  useEffect(() => {
    return () => {
      if (speechFallbackTimer.current != null) {
        window.clearTimeout(speechFallbackTimer.current);
      }
    };
  }, []);

  const handlePipelineEvent = (event: PipelineEvent) => {
    const patientText = event.data?.patient_text;
    if (
      event.phase === "turn" &&
      event.status === "started" &&
      typeof patientText === "string" &&
      patientText.trim()
    ) {
      appendMessage({
        id: createId("user"),
        role: "user",
        text: patientText.trim(),
      });
    }

    const spoken = event.data?.spoken_utterance;
    if (
      event.phase === "supervisor" &&
      event.status === "completed" &&
      typeof spoken === "string" &&
      spoken.trim() &&
      event.data?.action !== "build_final_query"
    ) {
      appendMessage({
        id: createId("healia"),
        role: "healia",
        text: spoken.trim(),
      });
    }

    const stepId = stepIdForPipelinePhase(event.phase);
    if (stepId) {
      if (event.status === "started") {
        markProcessingStep(stepId, "active");
      }
      if (event.status === "completed" || event.status === "skipped") {
        markProcessingStep(stepId, "completed");
      }
    }

    // Enter processing + mute mic so patient can't barge in
    if (isProcessingStartEvent(event) && !navigatedToProcessing.current) {
      navigatedToProcessing.current = true;
      setMicEnabled(false);
      markProcessingStep("symptoms", "completed");
      markProcessingStep("references", "active");
      goToProcessing();
    }

    // Store guidance but keep LiveKit open for spoken reply
    if (isGuidanceReadyEvent(event) && !guidanceStored.current) {
      const results = event.data?.results as Record<string, unknown> | undefined;
      const mapped = mapBackendGuidanceToResult(results ?? null);
      if (mapped) {
        guidanceStored.current = true;
        setGuidanceResult(mapped);
        markProcessingStep("results", "active");

        const answer =
          typeof results?.spoken_answer === "string"
            ? results.spoken_answer.trim()
            : "";
        if (answer) {
          appendMessage({
            id: createId("healia"),
            role: "healia",
            text: answer,
          });
        }

        // Fallback if speech.completed never arrives
        speechFallbackTimer.current = window.setTimeout(() => {
          finishAndShowResults();
        }, SPEECH_FALLBACK_MS);
      }
    }

    // After Healia finishes speaking → Results, then disconnect
    if (isSpeechCompleteEvent(event) && guidanceStored.current) {
      markProcessingStep("results", "completed");
      finishAndShowResults();
    }
  };

  useDataChannel(PIPELINE_TOPIC, (msg) => {
    const event = parsePipelinePayload(msg.payload);
    if (!event) return;
    handlePipelineEvent(event);
  });

  return (
    <>
      <RoomAudioRenderer />
      <StartAudio label="Enable audio to hear Healia" />
    </>
  );
}

function LiveKitSessionInner({ children }: { children: ReactNode }) {
  const { setConnectionError } = useConsultation();

  const tokenSource = useMemo(
    () => TokenSource.endpoint(LIVEKIT_TOKEN_URL),
    [],
  );

  const roomName = useMemo(() => `healia-consult-${Date.now()}`, []);

  const room = useMemo(
    () =>
      new Room({
        audioCaptureDefaults: {
          autoGainControl: true,
          echoCancellation: true,
          noiseSuppression: false,
        },
      }),
    [],
  );

  const session = useSession(tokenSource, {
    room,
    roomName,
    agentName: HEALIA_AGENT_NAME,
  });

  useEffect(() => {
    let cancelled = false;

    session
      .start({
        tracks: {
          microphone: { enabled: true },
        },
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        console.error("Failed to start LiveKit consultation session:", error);
        setConnectionError(
          "We couldn't start the consultation. Make sure the backend API and Healia voice agent are running.",
        );
      });

    return () => {
      cancelled = true;
      void session.end();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <SessionProvider session={session}>
      <LiveKitBridge room={room} />
      {children}
    </SessionProvider>
  );
}

/**
 * Keeps LiveKit mounted across Session → Processing so pipeline events / speech are not lost.
 */
export function LiveKitConsultationShell({
  children,
}: {
  children: ReactNode;
}) {
  const { liveSessionActive, liveSessionKey } = useConsultation();

  if (!liveSessionActive) {
    return <>{children}</>;
  }

  return (
    <LiveKitSessionInner key={liveSessionKey}>{children}</LiveKitSessionInner>
  );
}
