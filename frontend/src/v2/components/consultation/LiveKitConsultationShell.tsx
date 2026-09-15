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
  parsePipelinePayload,
  stepIdForPipelinePhase,
  type PipelineEvent,
} from "@/v2/lib/pipeline";
import { mapAgentStateToVoiceState } from "@/v2/lib/voiceState";

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
    micEnabled,
    guidanceReady,
    endLiveSession,
  } = useConsultation();

  const { state } = useVoiceAssistant();
  const { send: sendChat } = useChat();
  const navigatedToProcessing = useRef(false);
  const navigatedToResults = useRef(false);

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

    if (isProcessingStartEvent(event) && !navigatedToProcessing.current) {
      navigatedToProcessing.current = true;
      markProcessingStep("symptoms", "completed");
      markProcessingStep("references", "active");
      goToProcessing();
    }

    if (isGuidanceReadyEvent(event) && !navigatedToResults.current) {
      const results = event.data?.results as Record<string, unknown> | undefined;
      const mapped = mapBackendGuidanceToResult(results ?? null);
      if (mapped) {
        setGuidanceResult(mapped);
        navigatedToResults.current = true;

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

        window.setTimeout(() => {
          goToResults();
          // Disconnect after Results mount so room teardown does not race navigation.
          window.setTimeout(() => {
            endLiveSession();
          }, 400);
        }, 600);
      }
    }
  };

  useDataChannel(PIPELINE_TOPIC, (msg) => {
    const event = parsePipelinePayload(msg.payload);
    if (!event) return;
    handlePipelineEvent(event);
  });

  useEffect(() => {
    if (guidanceReady && !navigatedToResults.current) {
      navigatedToResults.current = true;
      goToResults();
      window.setTimeout(() => endLiveSession(), 400);
    }
  }, [endLiveSession, goToResults, guidanceReady]);

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
 * Keeps LiveKit mounted across Session → Processing so pipeline events are not lost.
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
