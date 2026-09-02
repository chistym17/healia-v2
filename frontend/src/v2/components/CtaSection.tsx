import { V2Button } from "./V2Button";

export function CtaSection() {
  return (
    <section className="bg-healia-bg-secondary">
      <div className="mx-auto max-w-page px-5 py-16 md:px-8 md:py-20 lg:px-12">
        <div className="rounded-xl border border-healia-border bg-healia-brand px-8 py-12 text-center md:px-16 md:py-16">
          <h2 className="text-2xl font-semibold tracking-tight text-white md:text-3xl">
            Ready to get started?
          </h2>
          <div className="mt-8">
            <V2Button
              to="/v2/consultation"
              className="bg-white text-healia-brand hover:bg-healia-brand-light focus-visible:ring-white"
            >
              Start Consultation
            </V2Button>
          </div>
        </div>
      </div>
    </section>
  );
}
