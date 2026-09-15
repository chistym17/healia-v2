import { useEffect, useRef } from "react";
import type { TranscriptMessage } from "@/v2/types/consultation";

type ConsultationTranscriptProps = {
  messages: TranscriptMessage[];
};

export function ConsultationTranscript({
  messages,
}: ConsultationTranscriptProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="mx-auto w-full max-w-consultation flex-1 px-5 py-4 md:px-0">
        <p className="text-center text-sm text-healia-text-muted">
          Your conversation will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-consultation flex-1 flex-col border-t border-healia-border-subtle px-5 pt-4 md:px-0">
      <div
        ref={scrollRef}
        className="healia-transcript-scroll max-h-[min(42vh,22rem)] flex-1 space-y-5 overflow-y-auto pr-1"
      >
        {messages.map((message) => (
          <div key={message.id}>
            <p
              className={`text-xs font-medium uppercase tracking-wide ${
                message.role === "healia"
                  ? "text-healia-brand"
                  : "text-healia-text-muted"
              }`}
            >
              {message.role === "healia" ? "Healia" : "You"}
            </p>
            <p className="mt-1 text-sm leading-relaxed text-healia-text">
              {message.text}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
