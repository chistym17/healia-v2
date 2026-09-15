import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Clock,
  HeartPulse,
  Info,
  MicOff,
  Shield,
} from "lucide-react";
import { ConsultationLayout } from "@/v2/components/consultation/ConsultationLayout";
import { ProcessingSteps } from "@/v2/components/consultation/ProcessingSteps";
import { useConsultation } from "@/v2/context/ConsultationContext";

const ACTIVE_COPY: Record<
  string,
  { title: string; body: string }
> = {
  symptoms: {
    title: "Understanding your conversation",
    body: "Reviewing the symptoms and answers you shared so nothing important is missed.",
  },
  references: {
    title: "Looking up medical references",
    body: "Searching trusted sources related to what you described — not guessing from memory alone.",
  },
  results: {
    title: "Preparing your guidance",
    body: "Building your summary, practical next steps, warning signs, and when to seek care. You may hear a short spoken summary when ready.",
  },
};

function formatElapsed(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  if (m <= 0) return `${s}s`;
  return `${m}m ${s.toString().padStart(2, "0")}s`;
}

export default function ProcessingPage() {
  const {
    processingSteps,
    completedStepIds,
    activeStepId,
    guidanceReady,
    connectionError,
  } = useConsultation();

  const [elapsedSec, setElapsedSec] = useState(0);

  useEffect(() => {
    const started = Date.now();
    const id = window.setInterval(() => {
      setElapsedSec(Math.floor((Date.now() - started) / 1000));
    }, 1000);
    return () => window.clearInterval(id);
  }, []);

  // Results navigation is handled by LiveKit bridge after speech.completed
  // so the spoken reply is not cut off.

  const currentStepId =
    activeStepId ||
    processingSteps.find((s) => !completedStepIds.includes(s.id))?.id ||
    "results";

  const currentCopy = ACTIVE_COPY[currentStepId] ?? ACTIVE_COPY.results;

  const waitHint = useMemo(() => {
    if (guidanceReady) {
      return "Guidance is ready — Healia may speak a short summary, then your results open.";
    }
    if (elapsedSec < 20) {
      return "Usually takes about 15–60 seconds. Please stay on this page.";
    }
    if (elapsedSec < 60) {
      return "Still working — checking references and preparing your guidance.";
    }
    return "Taking longer than usual. Please wait — Healia is still preparing your results.";
  }, [elapsedSec, guidanceReady]);

  return (
    <ConsultationLayout>
      <div className="mx-auto flex h-[calc(100vh-3.5rem)] max-w-page flex-col px-5 py-5 md:px-8 md:py-6 lg:px-12">
        {/* Compact header */}
        <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-xs font-medium uppercase tracking-widest text-healia-brand">
              Almost done
            </p>
            <h1 className="mt-1 text-xl font-semibold tracking-tight text-healia-text md:text-2xl">
              Preparing your health guidance
            </h1>
          </div>
          <div className="flex items-center gap-2 rounded-lg border border-healia-border bg-healia-bg-secondary px-3 py-2">
            <Clock className="h-4 w-4 text-healia-brand" strokeWidth={1.75} />
            <div>
              <p className="text-[10px] uppercase tracking-wide text-healia-text-muted">
                Waiting
              </p>
              <p className="text-sm font-semibold tabular-nums text-healia-text">
                {formatElapsed(elapsedSec)}
              </p>
            </div>
          </div>
        </div>

        {/* Left / right cards — fit viewport, minimal scroll */}
        <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-2 lg:gap-5">
          {/* Left: status + notes */}
          <div className="flex min-h-0 flex-col gap-4">
            <section className="flex flex-1 flex-col rounded-xl border border-healia-brand/20 bg-healia-brand-light/40 p-5 md:p-6">
              <div className="flex items-center gap-2">
                <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-healia-brand text-white">
                  <HeartPulse className="h-4 w-4" strokeWidth={1.75} />
                </span>
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-healia-brand">
                    What Healia is doing now
                  </p>
                  <h2 className="text-lg font-semibold text-healia-text">
                    {connectionError ? "Something went wrong" : currentCopy.title}
                  </h2>
                </div>
              </div>

              <p className="mt-4 text-sm leading-relaxed text-healia-text-secondary">
                {connectionError || currentCopy.body}
              </p>

              {!connectionError && (
                <div className="mt-auto space-y-3 pt-5">
                  <div className="flex items-start gap-2.5 rounded-lg border border-healia-border/80 bg-healia-bg-secondary/90 px-3 py-2.5">
                    <MicOff
                      className="mt-0.5 h-4 w-4 shrink-0 text-healia-text-muted"
                      strokeWidth={1.75}
                    />
                    <p className="text-xs leading-relaxed text-healia-text-secondary">
                      Your microphone is muted while guidance is prepared, so
                      talking won&apos;t interrupt Healia.
                    </p>
                  </div>
                  <div className="flex items-start gap-2.5 rounded-lg border border-healia-info/20 bg-healia-info/[0.06] px-3 py-2.5">
                    <Info
                      className="mt-0.5 h-4 w-4 shrink-0 text-healia-info"
                      strokeWidth={1.75}
                    />
                    <p className="text-xs leading-relaxed text-healia-text-secondary">
                      {waitHint}
                    </p>
                  </div>
                </div>
              )}
            </section>

            <aside className="rounded-xl border border-healia-border-subtle bg-healia-bg-secondary p-4 md:p-5">
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-healia-brand" strokeWidth={1.75} />
                <p className="text-sm font-medium text-healia-text">Please note</p>
              </div>
              <ul className="mt-3 space-y-2 text-xs leading-relaxed text-healia-text-secondary">
                <li className="flex gap-2">
                  <span className="text-healia-brand">·</span>
                  Stay on this page — results open automatically when ready.
                </li>
                <li className="flex gap-2">
                  <span className="text-healia-brand">·</span>
                  This is educational guidance, not a medical diagnosis.
                </li>
                <li className="flex gap-2">
                  <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-healia-warning" strokeWidth={1.75} />
                  <span>
                    If this feels like an emergency, seek urgent care now.
                  </span>
                </li>
              </ul>
            </aside>
          </div>

          {/* Right: progress steps */}
          <section className="flex min-h-0 flex-col rounded-xl border border-healia-border bg-healia-bg-secondary p-5 md:p-6">
            <div className="mb-4 flex items-center justify-between gap-2">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-wider text-healia-text-muted">
                  Progress
                </p>
                <h2 className="text-lg font-semibold text-healia-text">
                  Guidance pipeline
                </h2>
              </div>
              {guidanceReady && (
                <span className="rounded-md bg-healia-success/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-healia-success">
                  Ready
                </span>
              )}
            </div>

            {connectionError ? (
              <p className="text-sm text-healia-danger">{connectionError}</p>
            ) : (
              <div className="min-h-0 flex-1">
                <ProcessingSteps
                  steps={processingSteps}
                  completedStepIds={completedStepIds}
                  activeStepId={activeStepId}
                  compact
                />
              </div>
            )}

            <p className="mt-4 border-t border-healia-border-subtle pt-3 text-xs text-healia-text-muted">
              Your consultation conversation is complete. Healia is finishing
              evidence-based guidance for you to read next.
            </p>
          </section>
        </div>
      </div>
    </ConsultationLayout>
  );
}
