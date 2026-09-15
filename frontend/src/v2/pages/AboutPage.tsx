import { V2Layout } from "@/v2/components/V2Layout";
import { V2Button } from "@/v2/components/V2Button";

const principles = [
  {
    title: "Calm and clear",
    body: "Healia is built for moments when you feel unwell and need direction — not a noisy chatbot experience.",
  },
  {
    title: "Evidence-aware",
    body: "Guidance is prepared with reference to medical knowledge sources, then shaped into practical next steps.",
  },
  {
    title: "Honest about limits",
    body: "Healia does not diagnose, prescribe, or replace a clinician. It helps you understand what to do next.",
  },
];

export default function AboutPage() {
  return (
    <V2Layout footer="compact">
      <div className="mx-auto w-full max-w-page px-5 py-10 md:px-8 md:py-12 lg:px-12">
        <div className="max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-healia-brand">
            About
          </p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-healia-text md:text-4xl">
            A calm health consultation assistant
          </h1>
          <p className="mt-4 text-base leading-relaxed text-healia-text-secondary md:text-lg">
            Healia helps you describe how you feel, answers focused follow-up
            questions, and prepares clear educational guidance — including what
            may be going on, what you can do now, and when to seek care.
          </p>
        </div>

        <div className="mt-12 grid gap-8 border-t border-healia-border-subtle pt-10 lg:grid-cols-[1.1fr_0.9fr] lg:gap-14">
          <section className="space-y-8">
            <div>
              <h2 className="text-xs font-semibold uppercase tracking-[0.14em] text-healia-brand">
                How it works
              </h2>
              <ol className="mt-4 space-y-4 text-sm leading-relaxed text-healia-text-secondary md:text-base">
                <li className="flex gap-3">
                  <span className="w-6 shrink-0 font-semibold tabular-nums text-healia-brand">
                    01
                  </span>
                  <span>
                    You start a consultation and speak about your symptoms in a
                    short voice conversation.
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="w-6 shrink-0 font-semibold tabular-nums text-healia-brand">
                    02
                  </span>
                  <span>
                    Healia asks one careful question at a time to understand what
                    matters most.
                  </span>
                </li>
                <li className="flex gap-3">
                  <span className="w-6 shrink-0 font-semibold tabular-nums text-healia-brand">
                    03
                  </span>
                  <span>
                    Your guidance is prepared and saved to your account so you can
                    revisit it later.
                  </span>
                </li>
              </ol>
            </div>

            <div>
              <h2 className="text-xs font-semibold uppercase tracking-[0.14em] text-healia-brand">
                What Healia is not
              </h2>
              <ul className="mt-4 space-y-2.5 text-sm leading-relaxed text-healia-text-secondary md:text-base">
                <li className="flex gap-2">
                  <span className="text-healia-brand">·</span>
                  Not a doctor, clinic, or emergency service
                </li>
                <li className="flex gap-2">
                  <span className="text-healia-brand">·</span>
                  Not a medical diagnosis or treatment plan
                </li>
                <li className="flex gap-2">
                  <span className="text-healia-brand">·</span>
                  Not a substitute for professional medical advice
                </li>
              </ul>
            </div>
          </section>

          <aside className="space-y-5">
            {principles.map((item) => (
              <div
                key={item.title}
                className="rounded-xl border border-healia-border bg-healia-bg-secondary px-5 py-4"
              >
                <h3 className="text-sm font-semibold text-healia-text">
                  {item.title}
                </h3>
                <p className="mt-1.5 text-sm leading-relaxed text-healia-text-secondary">
                  {item.body}
                </p>
              </div>
            ))}
          </aside>
        </div>

        <div className="mt-12 flex flex-col gap-3 border-t border-healia-border-subtle pt-8 sm:flex-row">
          <V2Button to="/consultation">Start Consultation</V2Button>
          <V2Button to="/privacy" variant="secondary">
            Read Privacy
          </V2Button>
        </div>
      </div>
    </V2Layout>
  );
}
