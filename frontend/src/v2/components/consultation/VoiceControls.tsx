import { Mic, MicOff, Send } from "lucide-react";
import { useState } from "react";
import type { VoiceState } from "@/v2/types/consultation";

type VoiceControlsProps = {
  voiceState: VoiceState;
  micEnabled: boolean;
  onToggleMic: () => void;
  onSendText: (text: string) => void;
};

export function VoiceControls({
  voiceState,
  micEnabled,
  onToggleMic,
  onSendText,
}: VoiceControlsProps) {
  const [text, setText] = useState("");
  const [showTextInput, setShowTextInput] = useState(false);
  const micBlocked = voiceState === "error";

  const handleSend = () => {
    if (!text.trim()) return;
    onSendText(text);
    setText("");
  };

  return (
    <div className="mx-auto w-full max-w-consultation px-5 pb-8 md:px-0">
      <div className="flex flex-col items-center gap-4">
        <button
          type="button"
          onClick={onToggleMic}
          disabled={micBlocked}
          aria-label={micEnabled ? "Mute microphone" : "Unmute microphone"}
          className={`flex h-14 w-14 items-center justify-center rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-healia-brand focus-visible:ring-offset-2 disabled:opacity-50 ${
            micEnabled
              ? "bg-healia-brand text-white hover:bg-healia-brand-dark"
              : "bg-healia-danger text-white hover:bg-healia-danger/90"
          }`}
        >
          {micEnabled ? (
            <Mic className="h-6 w-6" strokeWidth={1.75} />
          ) : (
            <MicOff className="h-6 w-6" strokeWidth={1.75} />
          )}
        </button>

        <p className="text-xs text-healia-text-muted">
          {micEnabled ? "Microphone on — speak naturally" : "Microphone muted"}
        </p>

        <button
          type="button"
          onClick={() => setShowTextInput((v) => !v)}
          className="text-xs text-healia-text-muted transition-colors hover:text-healia-text-secondary"
        >
          {showTextInput ? "Hide text input" : "Type instead"}
        </button>
      </div>

      {showTextInput && (
        <div className="mt-4 flex gap-2">
          <input
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Describe your symptoms…"
            className="flex-1 rounded-lg border border-healia-border bg-healia-bg-secondary px-4 py-2.5 text-sm text-healia-text placeholder:text-healia-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-healia-brand"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={!text.trim()}
            aria-label="Send message"
            className="flex h-10 w-10 items-center justify-center rounded-lg bg-healia-brand text-white transition-colors hover:bg-healia-brand-dark disabled:opacity-50"
          >
            <Send className="h-4 w-4" strokeWidth={1.75} />
          </button>
        </div>
      )}
    </div>
  );
}
