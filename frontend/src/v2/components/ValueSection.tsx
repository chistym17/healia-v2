import { ExternalLink } from "lucide-react";

function GuidanceDocumentPreview() {
  const sections = [
    {
      label: "Summary",
      sample: "You described dizziness when standing. No fever reported.",
    },
    {
      label: "What you can do now",
      sample: "Move slowly when standing. Stay hydrated. Rest if needed.",
    },
    {
      label: "Warning signs",
      sample: "Fainting, chest pain, or sudden severe headache.",
      isWarning: true,
    },
    {
      label: "When to seek care",
      sample: "See a clinician if symptoms persist beyond 48 hours.",
    },
  ];

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-xl border border-healia-border bg-healia-bg-secondary">
      <div className="border-b border-healia-border-subtle px-5 py-3.5">
        <p className="text-sm font-semibold text-healia-text">
          Your health guidance
        </p>
      </div>
      <div className="flex-1 space-y-4 px-5 py-5">
        {sections.map((section) => (
          <div key={section.label}>
            <p className="text-[10px] font-semibold uppercase tracking-wider text-healia-text-muted">
              {section.label}
            </p>
            {section.isWarning ? (
              <div className="mt-1.5 rounded-md border border-healia-danger/20 bg-healia-danger/[0.04] px-2.5 py-2">
                <p className="text-xs leading-relaxed text-healia-text-secondary">
                  {section.sample}
                </p>
              </div>
            ) : (
              <p className="mt-1.5 text-xs leading-relaxed text-healia-text-secondary">
                {section.sample}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function ReferencesPreview() {
  const refs = [
    { source: "Mayo Clinic", title: "Dizziness — symptoms & causes" },
    { source: "NHS", title: "Lightheadedness and dizziness" },
  ];

  return (
    <div className="flex h-full flex-col rounded-xl border border-healia-border bg-healia-bg-secondary p-5">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-healia-text-muted">
        References
      </p>
      <ul className="mt-3 space-y-3">
        {refs.map((ref) => (
          <li
            key={ref.title}
            className="flex items-start justify-between gap-2 border-b border-healia-border-subtle pb-3 last:border-0 last:pb-0"
          >
            <div>
              <p className="text-xs font-medium text-healia-text">
                {ref.title}
              </p>
              <p className="mt-0.5 text-[10px] text-healia-text-muted">
                {ref.source}
              </p>
            </div>
            <ExternalLink
              className="mt-0.5 h-3 w-3 shrink-0 text-healia-text-muted"
              strokeWidth={1.75}
            />
          </li>
        ))}
      </ul>
    </div>
  );
}

function HonestyPreview() {
  return (
    <div className="flex h-full flex-col justify-center rounded-xl border border-healia-border bg-healia-brand-light/50 p-5">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-healia-brand">
        Honest limits
      </p>
      <ul className="mt-3 space-y-2 text-xs leading-relaxed text-healia-text-secondary">
        <li>Possible explanations, not diagnoses.</li>
        <li>Urgent symptoms flagged clearly.</li>
      </ul>
    </div>
  );
}

function VoiceFirstPreview() {
  const waveformHeights = [18, 32, 24, 36, 28, 34, 20];

  return (
    <div className="flex items-center gap-5 rounded-xl border border-healia-border bg-healia-bg-secondary px-5 py-4">
      <div className="flex h-10 shrink-0 items-end gap-0.5">
        {waveformHeights.map((h, i) => (
          <div
            key={i}
            className="w-0.5 rounded-full bg-healia-brand/35"
            style={{ height: `${h}px` }}
          />
        ))}
      </div>
      <div>
        <p className="text-sm font-medium text-healia-text">Voice-first</p>
        <p className="mt-0.5 text-xs text-healia-text-muted">
          Talk naturally. Text is a fallback.
        </p>
      </div>
    </div>
  );
}

export function ValueSection() {
  return (
    <section className="bg-healia-bg">
      <div className="mx-auto max-w-page px-5 py-20 md:px-8 md:py-24 lg:px-12">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-medium uppercase tracking-widest text-healia-brand">
            Why Healia
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-healia-text md:text-4xl">
            Clear guidance, not a chat transcript
          </h2>
        </div>

        <div className="mt-12 grid gap-4 md:mt-14 md:grid-cols-2 md:grid-rows-[auto_auto_auto] lg:grid-cols-[1.4fr_1fr] lg:grid-rows-[auto_auto]">
          <div className="md:col-span-2 lg:col-span-1 lg:row-span-2">
            <GuidanceDocumentPreview />
          </div>
          <ReferencesPreview />
          <HonestyPreview />
        </div>

        <div className="mt-4">
          <VoiceFirstPreview />
        </div>
      </div>
    </section>
  );
}
