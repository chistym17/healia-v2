import { V2Layout } from "@/v2/components/V2Layout";
import { V2Button } from "@/v2/components/V2Button";

const expectations = [
  "A short voice conversation about your symptoms",
  "Focused follow-up questions from Healia",
  "Clear, structured guidance when you're done",
];

export default function StartConsultationPage() {
  return (
    <V2Layout>
      <div className="mx-auto max-w-content px-5 py-16 md:py-24 lg:px-0">
        <p className="text-sm font-medium uppercase tracking-widest text-healia-brand">
          Before you start
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-healia-text md:text-4xl">
          Start your consultation
        </h1>
        <p className="mt-4 text-lg text-healia-text-secondary">
          Healia will ask about your symptoms and prepare guidance you can act
          on.
        </p>

        <ul className="mt-8 space-y-3">
          {expectations.map((item) => (
            <li
              key={item}
              className="flex gap-3 text-base text-healia-text-secondary"
            >
              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-healia-brand" />
              {item}
            </li>
          ))}
        </ul>

        <p className="mt-8 text-sm text-healia-text-muted">
          Your conversation is private. Healia does not replace a doctor.
        </p>

        <div className="mt-10 flex flex-col gap-3 sm:flex-row">
          <V2Button to="/v2/consultation/session">Start Consultation</V2Button>
          <V2Button to="/v2" variant="secondary">
            Go Back
          </V2Button>
        </div>
      </div>
    </V2Layout>
  );
}
