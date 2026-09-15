import type { ReactNode } from "react";
import { ExternalLink } from "lucide-react";
import type { GuidanceResult } from "@/v2/types/consultation";

type GuidanceResultsProps = {
  guidance: GuidanceResult;
};

function ResultSection({
  title,
  children,
  variant = "default",
}: {
  title: string;
  children: ReactNode;
  variant?: "default" | "warning";
}) {
  return (
    <section>
      <h2 className="text-xs font-semibold uppercase tracking-wider text-healia-text-muted">
        {title}
      </h2>
      {variant === "warning" ? (
        <div className="mt-3 rounded-lg border border-healia-danger/20 bg-healia-danger/[0.04] px-4 py-3">
          {children}
        </div>
      ) : (
        <div className="mt-3">{children}</div>
      )}
    </section>
  );
}

export function GuidanceResults({ guidance }: GuidanceResultsProps) {
  return (
    <article className="space-y-8">
      <ResultSection title="Summary">
        <p className="text-base leading-relaxed text-healia-text-secondary">
          {guidance.summary}
        </p>
      </ResultSection>

      <ResultSection title="What may be going on">
        <p className="text-base leading-relaxed text-healia-text-secondary">
          {guidance.possibleConcerns}
        </p>
      </ResultSection>

      <ResultSection title="What you can do now">
        <ul className="space-y-2">
          {guidance.actions.map((action) => (
            <li
              key={action}
              className="flex gap-2 text-base leading-relaxed text-healia-text-secondary"
            >
              <span className="text-healia-brand">·</span>
              {action}
            </li>
          ))}
        </ul>
      </ResultSection>

      <ResultSection title="Warning signs" variant="warning">
        <p className="text-sm leading-relaxed text-healia-text-secondary">
          {guidance.warningSigns}
        </p>
      </ResultSection>

      <ResultSection title="When to seek medical care">
        <p className="text-base leading-relaxed text-healia-text-secondary">
          {guidance.seekCare}
        </p>
      </ResultSection>

      <ResultSection title="References">
        <ul className="space-y-3">
          {guidance.references.map((ref) => (
            <li
              key={ref.title}
              className="flex items-start justify-between gap-3 border-b border-healia-border-subtle pb-3 last:border-0 last:pb-0"
            >
              <div>
                <p className="text-sm font-medium text-healia-text">
                  {ref.title}
                </p>
                <p className="mt-0.5 text-xs text-healia-text-muted">
                  {ref.source}
                </p>
              </div>
              <ExternalLink
                className="mt-0.5 h-3.5 w-3.5 shrink-0 text-healia-text-muted"
                strokeWidth={1.75}
              />
            </li>
          ))}
        </ul>
      </ResultSection>
    </article>
  );
}
