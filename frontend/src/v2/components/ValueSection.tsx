import { Shield, BookOpen, HeartHandshake } from "lucide-react";
import type { LucideIcon } from "lucide-react";

const values: {
  icon: LucideIcon;
  title: string;
  description: string;
}[] = [
  {
    icon: HeartHandshake,
    title: "Calm and human",
    description:
      "A consultation experience that feels like talking to someone who listens — not filling out a form or chatting with a bot.",
  },
  {
    icon: BookOpen,
    title: "Evidence-based",
    description:
      "Guidance is grounded in medical references. You'll see the sources behind the recommendations.",
  },
  {
    icon: Shield,
    title: "Built for trust",
    description:
      "Clear about limitations, honest about uncertainty, and upfront about when professional care is needed.",
  },
];

export function ValueSection() {
  return (
    <section className="bg-healia-bg">
      <div className="mx-auto max-w-page px-5 py-20 md:px-8 md:py-24 lg:px-12">
        <div className="grid gap-12 lg:grid-cols-[1fr_1.2fr] lg:gap-20 lg:items-start">
          <div className="lg:sticky lg:top-28">
            <p className="text-sm font-medium uppercase tracking-widest text-healia-brand">
              Why Healia
            </p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight text-healia-text md:text-4xl">
              Healthcare guidance that feels professional
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-healia-text-secondary">
              Healia is designed for the moment when you don't feel well and
              aren't sure what to do — not as a flashy AI demo.
            </p>
          </div>

          <div className="space-y-6">
            {values.map((item) => (
              <article
                key={item.title}
                className="flex gap-5 rounded-xl border border-healia-border bg-healia-bg-secondary p-6 md:p-7"
              >
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-healia-brand-light">
                  <item.icon
                    className="h-5 w-5 text-healia-brand"
                    strokeWidth={1.75}
                  />
                </div>
                <div>
                  <h3 className="text-lg font-medium text-healia-text">
                    {item.title}
                  </h3>
                  <p className="mt-1.5 text-base leading-relaxed text-healia-text-secondary">
                    {item.description}
                  </p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
