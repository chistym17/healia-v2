import { useEffect, useRef, useState } from "react";
import { useVoiceAssistant } from "@livekit/components-react";
import type { TrackReference } from "@livekit/components-core";
import type { VoiceState } from "@/v2/types/consultation";
import { cn } from "@/lib/utils";

const STATE_LABELS: Record<VoiceState, string> = {
  connecting: "Joining",
  ready: "Connected",
  listening: "Your turn",
  thinking: "Thinking",
  speaking: "Healia is talking",
  error: "Connection error",
};

const STATE_HINTS: Record<VoiceState, string> = {
  connecting: "Healia is joining your consultation — please wait",
  ready: "You're connected. Speak when you're ready",
  listening: "Go ahead — Healia is listening",
  thinking: "Understanding what you shared",
  speaking: "Listen for a moment, then reply when it's your turn",
  error: "Please try again",
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

/** Soft elapsed copy while waiting for a cold agent start. */
function useConnectingElapsed(active: boolean) {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    if (!active) {
      setSeconds(0);
      return;
    }
    setSeconds(0);
    const id = window.setInterval(() => {
      setSeconds((s) => s + 1);
    }, 1000);
    return () => window.clearInterval(id);
  }, [active]);

  if (!active) return null;
  if (seconds < 4) return "Setting up your room…";
  if (seconds < 12) return "Waiting for Healia to join…";
  return "Almost there — Healia is warming up…";
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
  const isConnecting = state === "connecting";
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
      {(isSpeaking || isListening || isThinking || isConnecting) && (
        <>
          <span
            className={cn(
              "absolute inset-0 rounded-full border border-healia-brand/20",
              isSpeaking && "animate-healia-ring",
              (isListening || isConnecting) && "animate-healia-ring-slow",
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
              isConnecting && "animate-healia-ring-slow opacity-60",
            )}
          />
        </>
      )}

      <span
        className="absolute inset-6 rounded-full bg-healia-brand/20 transition-opacity duration-200"
        style={{
          opacity: speakGlow,
          transform: `scale(${speakScale})`,
          filter: "blur(10px)",
        }}
      />

      <div
        className={cn(
          "relative z-10 flex h-20 w-20 items-center justify-center rounded-full transition-all duration-200",
          state === "error"
            ? "bg-healia-danger/15 border border-healia-danger/30"
            : "bg-healia-brand-light border border-healia-brand/25",
          isSpeaking && "shadow-[0_0_24px_rgba(21,94,89,0.28)]",
          (isThinking || isConnecting) && "animate-pulse",
        )}
        style={{ transform: `scale(${speakScale})` }}
      >
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

        {isThinking || isConnecting ? (
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
  const liveState: VoiceState =
    agentState === "speaking"
      ? "speaking"
      : agentState === "listening"
        ? "listening"
        : agentState === "thinking"
          ? "thinking"
          : state === "connecting"
            ? "connecting"
            : state;

  return (
    <SparkOrb
      state={liveState}
      micEnabled={micEnabled}
      audioTrack={audioTrack}
    />
  );
}

function ConnectingSteps({ elapsedHint }: { elapsedHint: string | null }) {
  const steps = [
    "Connect to room",
    "Healia joins",
    "Greeting starts",
  ];

  return (
    <ol className="mt-5 w-full max-w-xs space-y-2 text-left" aria-hidden="true">
      {steps.map((label, i) => (
        <li
          key={label}
          className="flex items-center gap-2.5 text-xs text-healia-text-secondary"
        >
          <span
            className={cn(
              "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[10px] font-medium",
              i === 0
                ? "border-healia-brand/40 bg-healia-brand text-white"
                : i === 1
                  ? "border-healia-brand/50 bg-healia-brand-light text-healia-brand animate-pulse"
                  : "border-healia-border text-healia-text-muted",
            )}
          >
            {i + 1}
          </span>
          <span className={i === 1 ? "text-healia-brand font-medium" : undefined}>
            {label}
          </span>
        </li>
      ))}
      {elapsedHint ? (
        <li className="pt-1 text-center text-xs text-healia-text-muted">
          {elapsedHint}
        </li>
      ) : null}
    </ol>
  );
}

export function VoiceStateIndicator({
  state,
  micEnabled = true,
  liveAudio = false,
}: VoiceStateIndicatorProps) {
  const prevState = useRef(state);
  const [flashConnected, setFlashConnected] = useState(false);
  const connectingHint = useConnectingElapsed(state === "connecting");

  useEffect(() => {
    if (
      prevState.current === "connecting" &&
      (state === "speaking" || state === "listening" || state === "ready")
    ) {
      setFlashConnected(true);
      const t = window.setTimeout(() => setFlashConnected(false), 2200);
      prevState.current = state;
      return () => window.clearTimeout(t);
    }
    prevState.current = state;
  }, [state]);

  const label =
    flashConnected && state !== "connecting"
      ? "Joined"
      : STATE_LABELS[state];

  const hint =
    !micEnabled && state !== "error" && state !== "connecting"
      ? "Microphone is muted"
      : flashConnected && state === "speaking"
        ? "Healia joined — listen to the greeting"
        : flashConnected && (state === "listening" || state === "ready")
          ? "Joined — talk now when you're ready"
          : STATE_HINTS[state];

  return (
    <div
      className="flex flex-col items-center py-6 md:py-8"
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      {liveAudio ? (
        <LiveAgentOrb state={state} micEnabled={micEnabled} />
      ) : (
        <SparkOrb state={state} micEnabled={micEnabled} />
      )}

      <p
        className={cn(
          "mt-4 text-sm font-medium",
          state === "error" ? "text-healia-danger" : "text-healia-brand",
        )}
      >
        {label}
      </p>
      <p className="mt-1 max-w-sm text-center text-sm text-healia-text-secondary">
        {hint}
      </p>

      {state === "connecting" ? (
        <ConnectingSteps elapsedHint={connectingHint} />
      ) : null}
    </div>
  );
}
