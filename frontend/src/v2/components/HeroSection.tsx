import { V2Button } from "./V2Button";
import { ConsultationPreview } from "./ConsultationPreview";

const highlights = [
  "Evidence-based guidance",
  "Voice-first consultation",
  "Clear next steps",
];

export function HeroSection() {
  return (
    <section className="relative overflow-hidden">
      <div className="absolute inset-x-0 top-0 h-[480px] bg-healia-brand-light/40" />

      <div className="relative mx-auto max-w-page px-5 pt-14 pb-20 md:px-8 md:pt-20 md:pb-28 lg:px-12">
        <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
          <div>
            <p className="text-sm font-medium uppercase tracking-widest text-healia-brand">
              Health consultation assistant
            </p>

            <h1 className="mt-4 text-[2.5rem] font-semibold leading-[1.15] tracking-tight text-healia-text md:text-5xl lg:text-[3.25rem]">
              Understand your symptoms.{" "}
              <span className="text-healia-brand">Know what to do next.</span>
            </h1>

            <p className="mt-6 max-w-lg text-lg leading-relaxed text-healia-text-secondary">
              Healia helps you describe how you feel, asks the right
              questions, and gives you calm, evidence-based guidance you can
              actually use.
            </p>

            <ul className="mt-8 flex flex-wrap gap-2">
              {highlights.map((item) => (
                <li
                  key={item}
                  className="rounded-md border border-healia-border bg-healia-bg-secondary px-3 py-1.5 text-sm text-healia-text-secondary"
                >
                  {item}
                </li>
              ))}
            </ul>

            <div className="mt-10 flex flex-col gap-3 sm:flex-row sm:items-center">
              <V2Button to="/v2/consultation">Start Consultation</V2Button>
              <V2Button to="/v2/about" variant="secondary">
                Learn more
              </V2Button>
            </div>
          </div>

          <ConsultationPreview />
        </div>
      </div>
    </section>
  );
}
