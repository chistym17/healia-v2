import { Mic, MessageCircle, ClipboardList, Shield } from "lucide-react";
import { V2Layout } from "@/v2/components/V2Layout";
import { V2Button } from "@/v2/components/V2Button";

const steps = [
  {
    icon: Mic,
    title: "Talk through your symptoms",
    body: "A short voice conversation — speak naturally.",
  },
  {
    icon: MessageCircle,
    title: "Answer focused follow-ups",
    body: "Healia asks one clear question at a time.",
  },
  {
    icon: ClipboardList,
    title: "Get structured guidance",
    body: "Summary, next steps, and when to seek care.",
  },
];

export default function StartConsultationPage() {
  return (
    <V2Layout footer="compact">
      <div className="mx-auto flex w-full max-w-page flex-1 flex-col justify-center px-5 py-8 md:px-8 md:py-10 lg:px-12">
        <div className="grid items-center gap-8 lg:grid-cols-[1.15fr_1fr] lg:gap-14">
          <section>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-healia-brand">
              Before you start
            </p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-healia-text md:text-4xl md:leading-tight">
              Ready for your health consultation
            </h1>
            <p className="mt-4 max-w-lg text-base leading-relaxed text-healia-text-secondary md:text-lg">
              Healia will listen, ask focused questions, and prepare guidance
              you can act on — private to your account.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
              <V2Button to="/consultation/session">
                Start Consultation
              </V2Button>
              <V2Button to="/consultations" variant="secondary">
                View history
              </V2Button>
            </div>

            <div className="mt-6 flex items-start gap-2 text-xs leading-relaxed text-healia-text-muted">
              <Shield className="mt-0.5 h-3.5 w-3.5 shrink-0 text-healia-brand" strokeWidth={1.75} />
              <span>
                Educational guidance only — not a diagnosis. For emergencies,
                seek urgent care now.
              </span>
            </div>
          </section>

          <section className="rounded-xl border border-healia-border bg-healia-bg-secondary p-5 md:p-6">
            <p className="text-[11px] font-semibold uppercase tracking-wider text-healia-text-muted">
              What to expect
            </p>
            <ul className="mt-4 space-y-4">
              {steps.map((step, index) => {
                const Icon = step.icon;
                return (
                  <li key={step.title} className="flex gap-3.5">
                    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-healia-brand-light text-healia-brand">
                      <Icon className="h-4 w-4" strokeWidth={1.75} />
                    </span>
                    <div className="min-w-0 pt-0.5">
                      <p className="text-sm font-medium text-healia-text">
                        <span className="mr-1.5 tabular-nums text-healia-brand">
                          {String(index + 1).padStart(2, "0")}
                        </span>
                        {step.title}
                      </p>
                      <p className="mt-0.5 text-sm text-healia-text-secondary">
                        {step.body}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ul>
          </section>
        </div>
      </div>
    </V2Layout>
  );
}
