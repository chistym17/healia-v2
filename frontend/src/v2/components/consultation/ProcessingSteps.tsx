import { Check, Loader2 } from "lucide-react";
import type { ProcessingStep } from "@/v2/types/consultation";

const STEP_DETAILS: Record<string, string> = {
  symptoms:
    "Healia is organizing what you described — symptoms, timing, and important details from your conversation.",
  references:
    "Healia is checking trusted medical references that match your situation.",
  results:
    "Healia is writing clear guidance for you: summary, next steps, and when to seek care.",
};

type ProcessingStepsProps = {
  steps: ProcessingStep[];
  completedStepIds: string[];
  activeStepId: string | null;
};

export function ProcessingSteps({
  steps,
  completedStepIds,
  activeStepId,
}: ProcessingStepsProps) {
  return (
    <ol className="space-y-4">
      {steps.map((step, index) => {
        const isComplete = completedStepIds.includes(step.id);
        const isActive = activeStepId === step.id;
        const detail = STEP_DETAILS[step.id];

        return (
          <li
            key={step.id}
            className={`rounded-xl border px-4 py-4 transition-colors md:px-5 ${
              isActive
                ? "border-healia-brand/25 bg-healia-brand-light/50"
                : isComplete
                  ? "border-healia-border-subtle bg-healia-bg-secondary"
                  : "border-healia-border-subtle bg-transparent"
            }`}
          >
            <div className="flex items-start gap-3">
              <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center">
                {isComplete ? (
                  <Check
                    className="h-5 w-5 text-healia-success"
                    strokeWidth={2}
                  />
                ) : isActive ? (
                  <Loader2
                    className="h-5 w-5 animate-spin text-healia-brand"
                    strokeWidth={2}
                  />
                ) : (
                  <span className="flex h-5 w-5 items-center justify-center rounded-full border border-healia-border text-[10px] font-medium text-healia-text-muted">
                    {index + 1}
                  </span>
                )}
              </span>

              <div className="min-w-0 flex-1">
                <p
                  className={`text-base font-medium ${
                    isComplete || isActive
                      ? "text-healia-text"
                      : "text-healia-text-muted"
                  }`}
                >
                  {step.label}
                </p>
                {detail && (isActive || isComplete) && (
                  <p
                    className={`mt-1 text-sm leading-relaxed ${
                      isActive
                        ? "text-healia-text-secondary"
                        : "text-healia-text-muted"
                    }`}
                  >
                    {detail}
                  </p>
                )}
                {isActive && (
                  <p className="mt-2 text-xs font-medium uppercase tracking-wide text-healia-brand">
                    In progress
                  </p>
                )}
              </div>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
