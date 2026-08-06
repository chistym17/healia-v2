import { useEffect, useMemo, useState } from "react";
import {
  BarVisualizer,
  ControlBar,
  RoomAudioRenderer,
  SessionProvider,
  StartAudio,
  useSession,
  useVoiceAssistant,
} from "@livekit/components-react";
import { TokenSource } from "livekit-client";
import { Link } from "react-router-dom";
import "@livekit/components-styles";

const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

function VoiceInterface() {
  const { state, audioTrack } = useVoiceAssistant();

  return (
    <div className="w-full max-w-lg rounded-2xl bg-white p-8 shadow-lg text-center space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Healia Voice Test</h1>
        <p className="mt-2 text-sm text-gray-600">
          Agent state: <span className="font-semibold text-blue-600">{state}</span>
        </p>
      </div>

      <div className="h-24 flex items-center justify-center">
        <BarVisualizer state={state} trackRef={audioTrack} barCount={7} />
      </div>

      <ControlBar
        controls={{
          microphone: true,
          camera: false,
          screenShare: false,
          chat: false,
          leave: true,
        }}
      />

      <RoomAudioRenderer />
      <StartAudio label="Enable audio playback" />

      <p className="text-xs text-gray-400">
        Allow microphone access, then speak after the agent greets you.
      </p>
    </div>
  );
}

function VoiceSession() {
  const tokenSource = useMemo(
    () => TokenSource.endpoint(`${apiUrl}/api/livekit/token`),
    [],
  );

  // Stable room name — Date.now() inline in render caused endless token fetches.
  const roomName = useMemo(() => `healia-test-${Date.now()}`, []);

  const session = useSession(tokenSource, {
    roomName,
    agentName: "healia",
  });

  useEffect(() => {
    session.start().catch((error) => {
      console.error("Failed to start LiveKit session:", error);
    });

    return () => {
      session.end();
    };
    // Start once on mount (LiveKit Session API pattern).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <SessionProvider session={session}>
      <VoiceInterface />
    </SessionProvider>
  );
}

const LiveVoicePage = () => {
  const [started, setStarted] = useState(false);

  return (
    <main className="min-h-screen bg-slate-100 flex flex-col items-center justify-center gap-4 p-6">
      <Link to="/" className="text-sm text-blue-600 hover:underline">
        ← Back home
      </Link>

      {!started ? (
        <div className="w-full max-w-lg rounded-2xl bg-white p-8 shadow-lg text-center space-y-4">
          <h1 className="text-2xl font-bold text-gray-900">Healia Live Voice</h1>
          <p className="text-gray-600 text-sm">
            Minimal LiveKit test. Make sure the agent worker and API are running.
          </p>
          <button
            type="button"
            onClick={() => setStarted(true)}
            className="rounded-lg bg-blue-600 px-6 py-3 text-white font-semibold hover:bg-blue-700"
          >
            Start voice session
          </button>
        </div>
      ) : (
        <VoiceSession />
      )}
    </main>
  );
};

export default LiveVoicePage;
