import { Mic } from "lucide-react";

export function ConsultationPreview() {
  return (
    <div
      className="relative mx-auto w-full max-w-md lg:max-w-none"
      aria-hidden="true"
    >
      <div className="rounded-xl border border-healia-border bg-healia-bg-secondary p-6 shadow-sm md:p-8">
        <div className="mb-6 flex items-center justify-between border-b border-healia-border-subtle pb-4">
          <span className="text-sm font-medium text-healia-text">Healia</span>
          <span className="rounded-md bg-healia-brand-light px-2.5 py-1 text-xs font-medium text-healia-brand">
            Listening
          </span>
        </div>

        <div className="flex flex-col items-center py-6">
          <div className="relative flex h-20 w-20 items-center justify-center rounded-full border border-healia-border bg-healia-brand-light">
            <Mic className="h-7 w-7 text-healia-brand" strokeWidth={1.75} />
            <span className="absolute inset-0 rounded-full border border-healia-brand/20 animate-pulse" />
          </div>
          <p className="mt-4 text-sm text-healia-text-secondary">
            Tell me what you're feeling
          </p>
        </div>

        <div className="space-y-4 border-t border-healia-border-subtle pt-6">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-healia-text-muted">
              You
            </p>
            <p className="mt-1 text-sm leading-relaxed text-healia-text">
              I've had a headache since this morning.
            </p>
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-healia-brand">
              Healia
            </p>
            <p className="mt-1 text-sm leading-relaxed text-healia-text-secondary">
              Can you tell me where the pain is located?
            </p>
          </div>
        </div>
      </div>

      <div className="absolute -bottom-4 -left-4 -z-10 h-full w-full rounded-xl bg-healia-brand-light/60" />
    </div>
  );
}
