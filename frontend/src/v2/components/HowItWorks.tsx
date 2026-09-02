import { Check, Loader2 } from "lucide-react";

const waveformHeights = [22, 38, 30, 44, 34, 40, 26];

function StepVoicePreview() {
  return (
    <div className="overflow-hidden rounded-lg border border-healia-border bg-healia-bg-secondary">
      <div className="flex items-center justify-between border-b border-healia-border-subtle px-4 py-2.5">
        <span className="text-xs font-medium text-healia-brand">Listening</span>
        <span className="text-[10px] text-healia-text-muted">Voice consultation</span>
      </div>
      <div className="px-4 py-5">
        <div className="flex h-10 items-end justify-center gap-0.5">
          {waveformHeights.map((h, i) => (
            <div
              key={i}
              className="w-0.5 rounded-full bg-healia-brand/30"
              style={{ height: `${h}px` }}
            />
          ))}
        </div>
        <p className="mt-3 text-center text-xs italic text-healia-text-secondary">
          &ldquo;I've felt dizzy on and off for two days&hellip;&rdquo;
        </p>
      </div>
    </div>
  );
}

function StepConversationPreview() {
  return (
    <div className="overflow-hidden rounded-lg border border-healia-border bg-healia-bg-secondary px-4 py-4">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-healia-text-muted">
        Understanding your symptoms
      </p>
      <div className="mt-4 space-y-4">
        <div>
          <p className="text-[10px] font-medium text-healia-text-muted">You</p>
          <p className="mt-0.5 text-xs leading-relaxed text-healia-text">
            It gets worse when I stand up quickly.
          </p>
        </div>
        <div>
          <p className="text-[10px] font-medium text-healia-brand">Healia</p>
          <p className="mt-0.5 text-xs leading-relaxed text-healia-text-secondary">
            Any nausea, fever, or vision changes?
          </p>
        </div>
      </div>
    </div>
  );
}

function StepGuidancePreview() {
  return (
    <div className="overflow-hidden rounded-lg border border-healia-border bg-healia-bg-secondary">
      <div className="border-b border-healia-border-subtle px-4 py-2.5">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-healia-text-muted">
          Preparing your guidance
        </p>
        <ul className="mt-2 space-y-1.5">
          {[
            "Reviewing your symptoms",
            "Checking medical references",
            "Preparing your results",
          ].map((label, i) => (
            <li key={label} className="flex items-center gap-2">
              {i < 2 ? (
                <Check className="h-3 w-3 text-healia-success" strokeWidth={2.5} />
              ) : (
                <Loader2 className="h-3 w-3 animate-spin text-healia-brand" strokeWidth={2} />
              )}
              <span className="text-xs text-healia-text-secondary">{label}</span>
            </li>
          ))}
        </ul>
      </div>
      <div className="space-y-3 px-4 py-4">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wider text-healia-text-muted">
            Summary
          </p>
          <p className="mt-1 text-xs leading-relaxed text-healia-text-secondary">
            Possible orthostatic symptoms. See a clinician if persistent.
          </p>
        </div>
        <div className="rounded-md border border-healia-danger/15 bg-healia-danger/[0.04] px-2.5 py-2">
          <p className="text-[10px] font-semibold text-healia-text">
            When to seek care
          </p>
          <p className="mt-0.5 text-[10px] leading-relaxed text-healia-text-secondary">
            Fainting, chest pain, or severe headache.
          </p>
        </div>
      </div>
    </div>
  );
}

const steps = [
  {
    phase: "Start",
    title: "Describe your symptoms",
    description: "Talk by voice. No forms.",
    preview: <StepVoicePreview />,
  },
  {
    phase: "Consultation",
    title: "Answer follow-up questions",
    description: "Adaptive questions based on your answers.",
    preview: <StepConversationPreview />,
  },
  {
    phase: "Guidance",
    title: "Get clear next steps",
    description: "Summary, actions, warnings, and references.",
    preview: <StepGuidancePreview />,
  },
];

export function HowItWorks() {
  return (
    <section className="border-y border-healia-border-subtle bg-healia-bg-secondary">
      <div className="mx-auto max-w-page px-5 py-20 md:px-8 md:py-28 lg:px-12">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-medium uppercase tracking-widest text-healia-brand">
            Your journey
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-healia-text md:text-4xl">
            How it works
          </h2>
        </div>

        <ol className="relative mt-16 md:mt-20">
          <div
            className="absolute left-[19px] top-3 hidden h-[calc(100%-2rem)] w-px bg-healia-border md:left-1/2 md:block md:-translate-x-px"
            aria-hidden="true"
          />

          {steps.map((step, index) => {
            const isEven = index % 2 === 1;

            return (
              <li
                key={step.phase}
                className="relative pb-16 last:pb-0 md:grid md:grid-cols-2 md:gap-x-12 md:gap-y-0 md:pb-24 md:last:pb-0"
              >
                <div
                  className="absolute left-0 top-1 flex h-10 w-10 items-center justify-center rounded-full border-2 border-healia-brand bg-healia-bg-secondary md:left-1/2 md:-translate-x-1/2"
                  aria-hidden="true"
                >
                  <span className="text-xs font-semibold text-healia-brand">
                    {index + 1}
                  </span>
                </div>

                {/* Text column */}
                <div
                  className={`pl-14 md:pl-0 ${
                    isEven
                      ? "md:col-start-2 md:row-start-1 md:pl-12"
                      : "md:col-start-1 md:row-start-1 md:pr-12 md:text-right"
                  }`}
                >
                  <p className="text-xs font-semibold uppercase tracking-widest text-healia-brand">
                    {step.phase}
                  </p>
                  <h3 className="mt-2 text-xl font-medium text-healia-text md:text-2xl">
                    {step.title}
                  </h3>
                  <p className="mt-2 text-sm text-healia-text-secondary">
                    {step.description}
                  </p>
                </div>

                {/* Preview column */}
                <div
                  className={`mt-6 pl-14 md:mt-0 md:pl-0 ${
                    isEven
                      ? "md:col-start-1 md:row-start-1 md:pr-12"
                      : "md:col-start-2 md:row-start-1 md:pl-12"
                  }`}
                >
                  {step.preview}
                </div>
              </li>
            );
          })}
        </ol>
      </div>
    </section>
  );
}
