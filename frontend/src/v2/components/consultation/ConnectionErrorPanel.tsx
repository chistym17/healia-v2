import { AlertTriangle } from "lucide-react";
import { V2Button } from "@/v2/components/V2Button";
import type { ConsultationError } from "@/v2/lib/consultationErrors";

type ConnectionErrorPanelProps = {
  error: ConsultationError;
  onRetry?: () => void;
  retryLabel?: string;
  secondaryTo?: string;
  secondaryLabel?: string;
  className?: string;
};

export function ConnectionErrorPanel({
  error,
  onRetry,
  retryLabel = "Try again",
  secondaryTo = "/",
  secondaryLabel = "Go back",
  className = "",
}: ConnectionErrorPanelProps) {
  return (
    <div
      role="alert"
      className={`mx-auto w-full max-w-md rounded-xl border border-healia-danger/20 bg-healia-danger/[0.04] px-5 py-5 ${className}`}
    >
      <div className="flex items-start gap-3">
        <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-healia-danger/10 text-healia-danger">
          <AlertTriangle className="h-4 w-4" strokeWidth={1.75} />
        </span>
        <div className="min-w-0">
          <h2 className="text-base font-semibold text-healia-text">
            {error.title}
          </h2>
          <p className="mt-1.5 text-sm leading-relaxed text-healia-text-secondary">
            {error.message}
          </p>
        </div>
      </div>

      <div className="mt-4 rounded-lg border border-healia-border bg-healia-bg-secondary/80 px-3.5 py-3">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-healia-text-muted">
          What you can do
        </p>
        <p className="mt-1.5 text-sm leading-relaxed text-healia-text-secondary">
          {error.fix}
        </p>
      </div>

      <div className="mt-5 flex flex-wrap justify-center gap-3">
        {onRetry ? (
          <V2Button className="px-4 py-2 text-sm" onClick={onRetry}>
            {retryLabel}
          </V2Button>
        ) : null}
        <V2Button
          to={secondaryTo}
          variant="secondary"
          className="px-4 py-2 text-sm"
        >
          {secondaryLabel}
        </V2Button>
      </div>
    </div>
  );
}
