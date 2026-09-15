import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ConsultationLayout } from "@/v2/components/consultation/ConsultationLayout";
import { ProcessingSteps } from "@/v2/components/consultation/ProcessingSteps";
import { useConsultation } from "@/v2/context/ConsultationContext";

const ACTIVE_COPY: Record<
  string,
  { title: string; body: string }
> = {
  symptoms: {
    title: "Understanding your conversation",
    body: "Healia is reviewing the symptoms and answers you shared so nothing important is missed.",
  },
  references: {
    title: "Looking up medical references",
    body: "Healia is searching trusted medical sources related to what you described — not guessing from memory alone.",
  },
  results: {
    title: "Preparing your guidance",
    body: "Healia is putting together a clear summary, practical next steps, warning signs, and when to seek care.",
  },
};

function formatElapsed(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  if (m <= 0) return `${s}s`;
  return `${m}m ${s.toString().padStart(2, "0")}s`;
}

export default function ProcessingPage() {
  const navigate = useNavigate();
  const {
    processingSteps,
    completedStepIds,
    activeStepId,
    guidanceReady,
    guidance,
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

  useEffect(() => {
    if (guidanceReady && guidance) {
      navigate("/v2/consultation/results");
    }
  }, [guidance, guidanceReady, navigate]);

  const currentStepId =
    activeStepId ||
    processingSteps.find((s) => !completedStepIds.includes(s.id))?.id ||
    "results";

  const currentCopy = ACTIVE_COPY[currentStepId] ?? ACTIVE_COPY.results;

  const waitHint = useMemo(() => {
    if (elapsedSec < 15) {
      return "This usually takes about 15–45 seconds.";
    }
    if (elapsedSec < 45) {
      return "Still working — checking references and preparing your guidance.";
    }
    return "Taking a bit longer than usual. Please stay on this page — Healia is still preparing your results.";
  }, [elapsedSec]);

  return (
    <ConsultationLayout>
      <div className="mx-auto max-w-content px-5 py-14 md:py-20 lg:px-0">
        <p className="text-sm font-medium uppercase tracking-widest text-healia-brand">
          Almost done
        </p>
        <h1 className="mt-3 text-2xl font-semibold tracking-tight text-healia-text md:text-3xl">
          Preparing your health guidance
        </h1>
        <p className="mt-3 max-w-xl text-base leading-relaxed text-healia-text-secondary">
          Your consultation is complete. Healia is now turning your conversation
          into clear, evidence-based guidance you can read and act on.
        </p>

        {/* Current activity card */}
        <div className="mt-10 rounded-xl border border-healia-border bg-healia-bg-secondary px-5 py-5 md:px-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-healia-text-muted">
                What Healia is doing now
              </p>
              <h2 className="mt-2 text-lg font-medium text-healia-text">
                {connectionError ? "Something went wrong" : currentCopy.title}
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-healia-text-secondary">
                {connectionError || currentCopy.body}
              </p>
            </div>
            {!connectionError && (
              <div className="shrink-0 text-right">
                <p className="text-xs text-healia-text-muted">Time waiting</p>
                <p className="mt-1 font-medium tabular-nums text-healia-brand">
                  {formatElapsed(elapsedSec)}
                </p>
              </div>
            )}
          </div>

          {!connectionError && (
            <p className="mt-4 border-t border-healia-border-subtle pt-4 text-sm text-healia-text-secondary">
              {waitHint}
            </p>
          )}
        </div>

        {/* Steps */}
        {!connectionError && (
          <div className="mt-8">
            <p className="mb-4 text-sm font-medium text-healia-text">
              Progress
            </p>
            <ProcessingSteps
              steps={processingSteps}
              completedStepIds={completedStepIds}
              activeStepId={activeStepId}
            />
          </div>
        )}

        {/* User notes */}
        <aside className="mt-10 rounded-lg border border-healia-border-subtle bg-healia-bg px-5 py-4">
          <p className="text-sm font-medium text-healia-text">Please note</p>
          <ul className="mt-3 space-y-2 text-sm leading-relaxed text-healia-text-secondary">
            <li className="flex gap-2">
              <span className="text-healia-brand">·</span>
              You don&apos;t need to refresh or go back — results open
              automatically when ready.
            </li>
            <li className="flex gap-2">
              <span className="text-healia-brand">·</span>
              Healia is not diagnosing you. This is educational guidance based
              on what you shared and medical references.
            </li>
            <li className="flex gap-2">
              <span className="text-healia-brand">·</span>
              If you feel this is an emergency, stop and seek urgent medical
              care now.
            </li>
          </ul>
        </aside>
      </div>
    </ConsultationLayout>
  );
}
