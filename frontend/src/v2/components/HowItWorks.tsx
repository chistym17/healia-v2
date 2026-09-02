import { Mic, MessageSquare, ClipboardList } from "lucide-react";
import type { LucideIcon } from "lucide-react";

const steps: {
  number: string;
  icon: LucideIcon;
  title: string;
  description: string;
}[] = [
  {
    number: "01",
    icon: Mic,
    title: "Describe your symptoms",
    description:
      "Talk naturally about how you feel. Healia listens and understands — no long forms or medical jargon.",
  },
  {
    number: "02",
    icon: MessageSquare,
    title: "Answer a few questions",
    description:
      "Healia asks focused follow-ups based on what you've shared, adapting as it learns more about your situation.",
  },
  {
    number: "03",
    icon: ClipboardList,
    title: "Receive clear guidance",
    description:
      "Get a structured summary: what may be going on, what to do now, warning signs, and when to seek care.",
  },
];

export function HowItWorks() {
  return (
    <section className="border-y border-healia-border-subtle bg-healia-bg-secondary">
      <div className="mx-auto max-w-page px-5 py-20 md:px-8 md:py-24 lg:px-12">
        <div className="max-w-xl">
          <p className="text-sm font-medium uppercase tracking-widest text-healia-brand">
            Simple process
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-healia-text md:text-4xl">
            How it works
          </h2>
          <p className="mt-4 text-lg leading-relaxed text-healia-text-secondary">
            From symptoms to guidance in a single, calm conversation — not a
            checklist.
          </p>
        </div>

        <ol className="mt-14 grid gap-6 md:grid-cols-3 md:gap-8">
          {steps.map((step) => (
            <li
              key={step.number}
              className="group relative flex flex-col rounded-xl border border-healia-border bg-healia-bg p-6 md:p-8"
            >
              <div className="flex items-start justify-between">
                <div className="flex h-11 w-11 items-center justify-center rounded-lg border border-healia-border bg-healia-bg-secondary">
                  <step.icon
                    className="h-5 w-5 text-healia-brand"
                    strokeWidth={1.75}
                  />
                </div>
                <span className="text-sm font-medium tabular-nums text-healia-text-muted">
                  {step.number}
                </span>
              </div>

              <h3 className="mt-6 text-xl font-medium text-healia-text">
                {step.title}
              </h3>
              <p className="mt-2 flex-1 text-base leading-relaxed text-healia-text-secondary">
                {step.description}
              </p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
