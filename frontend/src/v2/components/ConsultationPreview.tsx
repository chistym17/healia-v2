import type { ReactNode } from "react";
import { AlertTriangle, Check } from "lucide-react";

const waveformHeights = [28, 44, 36, 52, 40, 48, 32, 46, 38];

function VoiceStrip() {
  return (
    <div className="border-b border-healia-border-subtle px-5 py-4 md:px-6">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-healia-brand opacity-30" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-healia-brand" />
          </span>
          <span className="text-xs font-medium text-healia-brand">Listening</span>
        </div>
        <span className="text-xs text-healia-text-muted">0:42</span>
      </div>

      <div
        className="mt-4 flex h-12 items-end justify-center gap-1"
        aria-hidden="true"
      >
        {waveformHeights.map((height, i) => (
          <div
            key={i}
            className="w-1 rounded-full bg-healia-brand/25"
            style={{ height: `${height}%` }}
          />
        ))}
      </div>

      <p className="mt-3 text-center text-sm italic text-healia-text-secondary">
        &ldquo;I've had a headache since this morning, mostly on the left
        side&hellip;&rdquo;
      </p>
    </div>
  );
}

function GuidanceSection({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div>
      <h4 className="text-[11px] font-semibold uppercase tracking-wider text-healia-text-muted">
        {title}
      </h4>
      <div className="mt-2">{children}</div>
    </div>
  );
}

function GuidancePreview() {
  return (
    <div className="px-5 py-5 md:px-6 md:py-6">
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="text-base font-semibold text-healia-text">
          Your health guidance
        </h3>
        <span className="shrink-0 text-xs text-healia-text-muted">
          Just now
        </span>
      </div>

      <div className="mt-5 space-y-5">
        <GuidanceSection title="Summary">
          <p className="text-sm leading-relaxed text-healia-text-secondary">
            Based on your symptoms, this may be a mild tension-type headache.
            No urgent warning signs were reported.
          </p>
        </GuidanceSection>

        <GuidanceSection title="What you can do now">
          <ul className="space-y-1.5 text-sm text-healia-text-secondary">
            <li className="flex gap-2">
              <span className="text-healia-brand">·</span>
              Rest in a quiet, dimly lit room
            </li>
            <li className="flex gap-2">
              <span className="text-healia-brand">·</span>
              Drink water and consider an OTC pain reliever
            </li>
          </ul>
        </GuidanceSection>

        <div className="rounded-lg border border-healia-danger/20 bg-healia-danger/[0.04] px-3.5 py-3">
          <div className="flex gap-2">
            <AlertTriangle
              className="mt-0.5 h-4 w-4 shrink-0 text-healia-danger"
              strokeWidth={1.75}
            />
            <div>
              <p className="text-xs font-semibold text-healia-text">
                Seek care if symptoms worsen
              </p>
              <p className="mt-0.5 text-xs leading-relaxed text-healia-text-secondary">
                Sudden severe pain, vision changes, or neck stiffness need
                prompt evaluation.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-5 flex items-center gap-2 border-t border-healia-border-subtle pt-4">
        <BookIcon />
        <p className="text-xs text-healia-text-muted">
          Grounded in 3 medical references
        </p>
      </div>
    </div>
  );
}

function BookIcon() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="shrink-0 text-healia-text-muted"
      aria-hidden="true"
    >
      <path d="M12 7v14" />
      <path d="M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z" />
    </svg>
  );
}

function ProcessingBadge() {
  const steps = [
    { label: "Symptoms reviewed", done: true },
    { label: "References checked", done: true },
    { label: "Guidance ready", done: true },
  ];

  return (
    <div className="absolute -right-3 top-8 z-10 hidden rounded-lg border border-healia-border bg-healia-bg-secondary px-3.5 py-3 shadow-sm sm:block md:-right-5">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-healia-text-muted">
        Preparing guidance
      </p>
      <ul className="mt-2.5 space-y-2">
        {steps.map((step) => (
          <li key={step.label} className="flex items-center gap-2">
            <Check
              className="h-3.5 w-3.5 text-healia-success"
              strokeWidth={2.5}
            />
            <span className="text-xs text-healia-text-secondary">
              {step.label}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function ConsultationPreview() {
  return (
    <div
      className="relative mx-auto w-full max-w-md lg:max-w-none lg:pr-6"
      aria-hidden="true"
    >
      <ProcessingBadge />

      <div className="overflow-hidden rounded-xl border border-healia-border bg-healia-bg-secondary shadow-sm">
        <VoiceStrip />
        <GuidancePreview />
      </div>

      <div className="absolute -bottom-3 -left-3 -z-10 h-[calc(100%-1rem)] w-[calc(100%-1rem)] rounded-xl border border-healia-brand/10 bg-healia-brand-light/50" />
    </div>
  );
}
