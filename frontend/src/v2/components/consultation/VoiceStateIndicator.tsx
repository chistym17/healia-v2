import { useEffect, useRef, useState } from "react";
import { useVoiceAssistant } from "@livekit/components-react";
import type { TrackReference } from "@livekit/components-core";
import type { VoiceState } from "@/v2/types/consultation";
import { cn } from "@/lib/utils";

const STATE_LABELS: Record<VoiceState, string> = {
  ready: "Ready",
  listening: "Listening",
  thinking: "Thinking",
  speaking: "Speaking",
  error: "Connection error",
};

function useTrackLevel(audioTrack: TrackReference | undefined, active: boolean) {
  const [level, setLevel] = useState(0);

  useEffect(() => {
    if (!active || !audioTrack?.publication?.track) {
      setLevel(0);
      return;
    }

    const track = audioTrack.publication.track;
    const mediaStream = track.mediaStream;
    if (!mediaStream) {
      setLevel(0.35);
      return;
    }

    let raf = 0;
    let ctx: AudioContext | null = null;
    try {
      ctx = new AudioContext();
      const source = ctx.createMediaStreamSource(mediaStream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.75;
      source.connect(analyser);
      const data = new Uint8Array(analyser.frequencyBinCount);

      const tick = () => {
        analyser.getByteFrequencyData(data);
        let sum = 0;
        for (let i = 0; i < data.length; i++) sum += data[i];
        const avg = sum / data.length / 255;
        setLevel(Math.min(1, avg * 2.2));
        raf = requestAnimationFrame(tick);
      };
      raf = requestAnimationFrame(tick);
    } catch {
      setLevel(0.4);
    }

    return () => {
      cancelAnimationFrame(raf);
      void ctx?.close();
    };
  }, [active, audioTrack]);

  return level;
}

type SparkOrbProps = {
  state: VoiceState;
  micEnabled?: boolean;
  audioTrack?: TrackReference;
  className?: string;
};

function SparkOrb({
  state,
  micEnabled = true,
  audioTrack,
  className,
}: SparkOrbProps) {
  const isSpeaking = state === "speaking";
  const isListening = state === "listening" && micEnabled;
  const isThinking = state === "thinking";
  const level = useTrackLevel(audioTrack, isSpeaking);

  const speakScale = isSpeaking ? 1 + level * 0.28 : 1;
  const speakGlow = isSpeaking ? 0.25 + level * 0.45 : 0;

  return (
    <div
      className={cn("relative flex h-32 w-32 items-center justify-center", className)}
      aria-hidden="true"
    >
      {/* Outer spark rings */}
      {(isSpeaking || isListening || isThinking) && (
        <>
          <span
            className={cn(
              "absolute inset-0 rounded-full border border-healia-brand/20",
              isSpeaking && "animate-healia-ring",
              isListening && "animate-healia-ring-slow",
              isThinking && "opacity-40",
            )}
            style={
              isSpeaking
                ? { transform: `scale(${1.05 + level * 0.2})` }
                : undefined
            }
          />
          <span
            className={cn(
              "absolute inset-3 rounded-full border border-healia-brand/15",
              isSpeaking && "animate-healia-ring-delay",
            )}
          />
        </>
      )}

      {/* Soft glow when agent talks */}
      <span
        className="absolute inset-6 rounded-full bg-healia-brand/20 transition-opacity duration-200"
        style={{
          opacity: speakGlow,
          transform: `scale(${speakScale})`,
          filter: "blur(10px)",
        }}
      />

      {/* Core ball */}
      <div
        className={cn(
          "relative z-10 flex h-20 w-20 items-center justify-center rounded-full transition-all duration-200",
          state === "error"
            ? "bg-healia-danger/15 border border-healia-danger/30"
            : "bg-healia-brand-light border border-healia-brand/25",
          isSpeaking && "shadow-[0_0_24px_rgba(21,94,89,0.28)]",
          isThinking && "animate-pulse",
        )}
        style={{ transform: `scale(${speakScale})` }}
      >
        {/* Inner spark flecks while speaking */}
        {isSpeaking && (
          <div className="absolute inset-0 overflow-hidden rounded-full">
            {[0, 1, 2, 3, 4, 5].map((i) => (
              <span
                key={i}
                className="absolute h-1 w-1 rounded-full bg-healia-brand/70 animate-healia-spark"
                style={{
                  left: `${18 + (i * 11) % 64}%`,
                  top: `${22 + (i * 17) % 56}%`,
                  animationDelay: `${i * 0.18}s`,
                  opacity: 0.35 + level * 0.5,
                }}
              />
            ))}
          </div>
        )}

        {isThinking ? (
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-healia-brand border-t-transparent" />
        ) : (
          <div
            className={cn(
              "rounded-full bg-healia-brand transition-all duration-150",
              isSpeaking ? "h-4 w-4" : isListening ? "h-3.5 w-3.5" : "h-2.5 w-2.5",
            )}
            style={
              isSpeaking
                ? { transform: `scale(${0.85 + level * 0.6})` }
                : undefined
            }
          />
        )}
      </div>
    </div>
  );
}

type VoiceStateIndicatorProps = {
  state: VoiceState;
  micEnabled?: boolean;
  /** When true, reads live agent audio from LiveKit SessionProvider. */
  liveAudio?: boolean;
};

function LiveAgentOrb({
  state,
  micEnabled,
}: {
  state: VoiceState;
  micEnabled?: boolean;
}) {
  const { audioTrack, state: agentState } = useVoiceAssistant();
  // Prefer LiveKit agent state when available for speaking animation
  const liveState: VoiceState =
    agentState === "speaking"
      ? "speaking"
      : agentState === "listening"
        ? "listening"
        : agentState === "thinking"
          ? "thinking"
          : state;

  return (
    <SparkOrb
      state={liveState}
      micEnabled={micEnabled}
      audioTrack={audioTrack}
    />
  );
}

export function VoiceStateIndicator({
  state,
  micEnabled = true,
  liveAudio = false,
}: VoiceStateIndicatorProps) {
  const hint =
    state === "error"
      ? "Please try again"
      : !micEnabled
        ? "Microphone is muted"
        : state === "ready"
          ? "Speak when you're ready — Healia is connected"
          : state === "listening"
            ? "Tell me what you're feeling"
            : state === "thinking"
              ? "Understanding your symptoms"
              : "Healia is responding";

  return (
    <div className="flex flex-col items-center py-6 md:py-8">
      {liveAudio ? (
        <LiveAgentOrb state={state} micEnabled={micEnabled} />
      ) : (
        <SparkOrb state={state} micEnabled={micEnabled} />
      )}

      <p
        className={`mt-4 text-sm font-medium ${
          state === "error" ? "text-healia-danger" : "text-healia-brand"
        }`}
      >
        {STATE_LABELS[state]}
      </p>
      <p className="mt-1 text-sm text-healia-text-secondary">{hint}</p>
    </div>
  );
}
