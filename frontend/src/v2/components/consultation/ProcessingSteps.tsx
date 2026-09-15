import { BookOpen, Check, ClipboardList, Loader2, Stethoscope } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { ProcessingStep } from "@/v2/types/consultation";

const STEP_META: Record<
  string,
  { detail: string; icon: LucideIcon; accent: string }
> = {
  symptoms: {
    detail: "Organizing symptoms and key details from your conversation.",
    icon: Stethoscope,
    accent: "text-healia-info bg-healia-info/10 border-healia-info/20",
  },
  references: {
    detail: "Checking trusted medical references for your situation.",
    icon: BookOpen,
    accent: "text-healia-brand bg-healia-brand-light border-healia-brand/20",
  },
  results: {
    detail: "Writing your summary, next steps, and care guidance.",
    icon: ClipboardList,
    accent: "text-healia-success bg-healia-success/10 border-healia-success/20",
  },
};

type ProcessingStepsProps = {
  steps: ProcessingStep[];
  completedStepIds: string[];
  activeStepId: string | null;
  compact?: boolean;
};

export function ProcessingSteps({
  steps,
  completedStepIds,
  activeStepId,
  compact = false,
}: ProcessingStepsProps) {
  return (
    <ol className={compact ? "space-y-2.5" : "space-y-3"}>
      {steps.map((step, index) => {
        const isComplete = completedStepIds.includes(step.id);
        const isActive = activeStepId === step.id;
        const meta = STEP_META[step.id];
        const Icon = meta?.icon;

        return (
          <li
            key={step.id}
            className={`flex items-start gap-3 rounded-xl border px-3.5 py-3 transition-colors ${
              isActive
                ? meta?.accent ||
                  "border-healia-brand/25 bg-healia-brand-light/60"
                : isComplete
                  ? "border-healia-success/20 bg-healia-success/[0.06]"
                  : "border-healia-border-subtle bg-healia-bg-secondary/80"
            }`}
          >
            <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-healia-bg-secondary border border-healia-border-subtle">
              {isComplete ? (
                <Check className="h-4 w-4 text-healia-success" strokeWidth={2.25} />
              ) : isActive ? (
                <Loader2
                  className="h-4 w-4 animate-spin text-healia-brand"
                  strokeWidth={2.25}
                />
              ) : Icon ? (
                <Icon className="h-4 w-4 text-healia-text-muted" strokeWidth={1.75} />
              ) : (
                <span className="text-[11px] font-medium text-healia-text-muted">
                  {index + 1}
                </span>
              )}
            </span>

            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between gap-2">
                <p
                  className={`text-sm font-medium ${
                    isComplete || isActive
                      ? "text-healia-text"
                      : "text-healia-text-muted"
                  }`}
                >
                  {step.label}
                </p>
                {isActive && (
                  <span className="shrink-0 rounded-md bg-healia-brand/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-healia-brand">
                    Now
                  </span>
                )}
                {isComplete && !isActive && (
                  <span className="shrink-0 text-[10px] font-medium uppercase tracking-wide text-healia-success">
                    Done
                  </span>
                )}
              </div>
              {meta?.detail && (
                <p
                  className={`mt-0.5 text-xs leading-relaxed ${
                    isActive
                      ? "text-healia-text-secondary"
                      : "text-healia-text-muted"
                  }`}
                >
                  {meta.detail}
                </p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
