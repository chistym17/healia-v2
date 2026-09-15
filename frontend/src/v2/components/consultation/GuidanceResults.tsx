import { AlertTriangle, Check, Copy, ExternalLink } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import type { GuidanceResult } from "@/v2/types/consultation";

type GuidanceResultsProps = {
  guidance: GuidanceResult;
};

function SectionLabel({ children }: { children: string }) {
  return (
    <h2 className="text-[11px] font-semibold uppercase tracking-[0.14em] text-healia-brand">
      {children}
    </h2>
  );
}

function formatGuidanceForCopy(guidance: GuidanceResult): string {
  const lines = [
    "Healia guidance",
    "",
    "Summary",
    guidance.summary,
    "",
    "What may be going on",
    guidance.possibleConcerns,
    "",
    "What you can do now",
    ...guidance.actions.map((action, i) => `${i + 1}. ${action}`),
    "",
    "Warning signs",
    guidance.warningSigns,
    "",
    "When to seek medical care",
    guidance.seekCare,
  ];

  if (guidance.references.length > 0) {
    lines.push(
      "",
      "References",
      ...guidance.references.map((ref) => `- ${ref.title} (${ref.source})`),
    );
  }

  lines.push(
    "",
    "Educational guidance only — not a medical diagnosis or treatment plan.",
  );

  return lines.join("\n");
}

export function GuidanceResults({ guidance }: GuidanceResultsProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(formatGuidanceForCopy(guidance));
      setCopied(true);
      toast.success("Summary copied");
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("Couldn't copy. Try selecting the text instead.");
    }
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-6 lg:flex-row lg:gap-10">
      {/* Main guidance — open typography, no cards */}
      <div className="flex min-h-0 min-w-0 flex-[1.35] flex-col">
        <div className="mb-3 flex justify-start">
          <button
            type="button"
            onClick={() => void handleCopy()}
            className="inline-flex items-center gap-1.5 rounded-lg border border-healia-border bg-healia-bg-secondary px-3 py-1.5 text-xs font-medium text-healia-text-secondary transition-colors hover:bg-healia-brand-light hover:text-healia-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-healia-brand"
          >
            {copied ? (
              <Check className="h-3.5 w-3.5 text-healia-success" strokeWidth={1.75} />
            ) : (
              <Copy className="h-3.5 w-3.5" strokeWidth={1.75} />
            )}
            {copied ? "Copied" : "Copy summary"}
          </button>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto healia-transcript-scroll pr-1">
          <p className="text-lg font-medium leading-snug tracking-tight text-healia-text md:text-xl md:leading-snug">
            {guidance.summary}
          </p>

          <div className="mt-7 border-t border-healia-border-subtle pt-6">
            <SectionLabel>What may be going on</SectionLabel>
            <p className="mt-2.5 text-sm leading-relaxed text-healia-text-secondary">
              {guidance.possibleConcerns}
            </p>
          </div>

          <div className="mt-7 border-t border-healia-border-subtle pt-6">
            <SectionLabel>What you can do now</SectionLabel>
            <ol className="mt-3 space-y-2.5">
              {guidance.actions.map((action, index) => (
                <li
                  key={action}
                  className="flex gap-3 text-sm leading-relaxed text-healia-text-secondary"
                >
                  <span className="w-5 shrink-0 text-xs font-semibold tabular-nums text-healia-brand">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  <span>{action}</span>
                </li>
              ))}
            </ol>
          </div>
        </div>
      </div>

      {/* Care column — one callout only */}
      <aside className="flex min-h-0 w-full shrink-0 flex-col gap-5 lg:w-[22rem] xl:w-96">
        <div className="rounded-xl border border-healia-danger/20 bg-healia-danger/[0.04] px-4 py-4">
          <div className="flex items-center gap-2">
            <AlertTriangle
              className="h-4 w-4 text-healia-danger"
              strokeWidth={1.75}
            />
            <h2 className="text-sm font-semibold text-healia-text">
              Warning signs
            </h2>
          </div>
          <p className="mt-2.5 text-sm leading-relaxed text-healia-text-secondary">
            {guidance.warningSigns}
          </p>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto healia-transcript-scroll">
          <SectionLabel>When to seek medical care</SectionLabel>
          <p className="mt-2.5 text-sm leading-relaxed text-healia-text-secondary">
            {guidance.seekCare}
          </p>

          {guidance.references.length > 0 && (
            <div className="mt-6 border-t border-healia-border-subtle pt-5">
              <SectionLabel>References</SectionLabel>
              <ul className="mt-3 space-y-3">
                {guidance.references.map((ref) => (
                  <li
                    key={`${ref.source}-${ref.title}`}
                    className="flex items-start gap-2"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-sm text-healia-text">{ref.title}</p>
                      <p className="mt-0.5 text-[11px] text-healia-text-muted">
                        {ref.source}
                      </p>
                    </div>
                    <ExternalLink
                      className="mt-0.5 h-3.5 w-3.5 shrink-0 text-healia-text-muted"
                      strokeWidth={1.75}
                      aria-hidden
                    />
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}
