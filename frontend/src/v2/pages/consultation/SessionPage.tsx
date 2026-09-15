import { useEffect } from "react";
import { ConsultationLayout } from "@/v2/components/consultation/ConsultationLayout";
import { ConnectionErrorPanel } from "@/v2/components/consultation/ConnectionErrorPanel";
import { VoiceStateIndicator } from "@/v2/components/consultation/VoiceStateIndicator";
import { ConsultationTranscript } from "@/v2/components/consultation/ConsultationTranscript";
import { VoiceControls } from "@/v2/components/consultation/VoiceControls";
import { V2Button } from "@/v2/components/V2Button";
import { useConsultation } from "@/v2/context/ConsultationContext";

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
    if (!sessionStarted && !liveSessionActive && !connectionError) {
      startSession();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleRetry = () => {
    startSession();
  };

  return (
    <ConsultationLayout
      agentRunning={liveSessionActive}
      onStopAgent={stopAgent}
      onStartAgent={startSession}
      onEnd={endConsultation}
    >
      <div className="mx-auto flex min-h-[calc(100vh-3.5rem)] max-w-consultation flex-col px-5 md:px-8">
        {connectionError ? (
          <div className="mt-10">
            <ConnectionErrorPanel
              error={connectionError}
              onRetry={handleRetry}
              secondaryTo="/consultation"
              secondaryLabel="Start over"
            />
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
