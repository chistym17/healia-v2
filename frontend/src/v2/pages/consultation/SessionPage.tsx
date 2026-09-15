import { ConsultationLayout } from "@/v2/components/consultation/ConsultationLayout";
import { VoiceStateIndicator } from "@/v2/components/consultation/VoiceStateIndicator";
import { ConsultationTranscript } from "@/v2/components/consultation/ConsultationTranscript";
import { VoiceControls } from "@/v2/components/consultation/VoiceControls";
import { V2Button } from "@/v2/components/V2Button";
import { useConsultation } from "@/v2/context/ConsultationContext";
import { useEffect } from "react";

export default function SessionPage() {
  const {
    voiceState,
    transcript,
    sessionStarted,
    liveSessionActive,
    startSession,
    stopAgent,
    toggleListening,
    endConsultation,
    sendTextMessage,
    connectionError,
    micEnabled,
  } = useConsultation();

  useEffect(() => {
    if (!sessionStarted && !liveSessionActive) {
      // Auto-start once when landing on session (first visit).
      startSession();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <ConsultationLayout
      agentRunning={liveSessionActive}
      onStopAgent={stopAgent}
      onStartAgent={startSession}
      onEnd={endConsultation}
    >
      <div className="mx-auto flex min-h-[calc(100vh-3.5rem)] max-w-consultation flex-col px-5 md:px-8">
        {connectionError ? (
          <div className="mx-auto mt-10 max-w-md rounded-lg border border-healia-danger/20 bg-healia-danger/[0.04] px-5 py-4 text-center">
            <p className="text-sm text-healia-text">{connectionError}</p>
            <div className="mt-4 flex justify-center gap-3">
              <V2Button
                className="px-4 py-2 text-sm"
                onClick={() => startSession()}
              >
                Try again
              </V2Button>
              <V2Button to="/" variant="secondary" className="px-4 py-2 text-sm">
                Go back
              </V2Button>
            </div>
          </div>
        ) : (
          <>
            <VoiceStateIndicator
              state={voiceState}
              micEnabled={micEnabled}
              liveAudio={liveSessionActive}
            />
            <ConsultationTranscript messages={transcript} />
            <div className="mt-auto">
              {liveSessionActive ? (
                <VoiceControls
                  voiceState={voiceState}
                  micEnabled={micEnabled}
                  onToggleMic={toggleListening}
                  onSendText={sendTextMessage}
                />
              ) : (
                <div className="px-5 pb-10 text-center md:px-0">
                  <p className="mb-4 text-sm text-healia-text-secondary">
                    Agent stopped. Start again to continue talking with Healia.
                  </p>
                  <V2Button onClick={startSession}>Start agent</V2Button>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </ConsultationLayout>
  );
}
