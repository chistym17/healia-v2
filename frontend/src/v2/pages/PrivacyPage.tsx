import { V2Layout } from "@/v2/components/V2Layout";
import { V2Button } from "@/v2/components/V2Button";

const sections = [
  {
    title: "What we collect",
    body: [
      "Account details you provide when you sign up, such as email and optional display name.",
      "Consultation content you share during a session, including transcript text and the guidance prepared for you.",
      "Basic technical information needed to run the service, such as authentication tokens and session identifiers.",
    ],
  },
  {
    title: "How we use your information",
    body: [
      "To provide your consultation and generate educational health guidance.",
      "To save completed consultations so you can reopen past results from your account.",
      "To keep the product secure, reliable, and working as intended.",
    ],
  },
  {
    title: "How your consultations are stored",
    body: [
      "Session history and guidance results are stored in our database and linked to your account.",
      "Only you can access your saved consultations when signed in.",
      "We do not sell your consultation content.",
    ],
  },
  {
    title: "Voice and processing",
    body: [
      "Voice consultations are handled in real time so Healia can listen and respond during the session.",
      "Transcript and guidance may be saved after a consultation completes so you can review them later.",
      "Third-party infrastructure (for example voice transport and authentication) may process data as needed to deliver the service.",
    ],
  },
  {
    title: "Your choices",
    body: [
      "You can sign out of your account at any time.",
      "You can choose not to start a consultation if you prefer not to share symptoms.",
      "If you need a consultation removed from your history, contact us and we will help where possible.",
    ],
  },
  {
    title: "Important medical notice",
    body: [
      "Healia provides educational guidance only. It is not medical advice, a diagnosis, or emergency care.",
      "If you think you may be experiencing a medical emergency, contact local emergency services immediately.",
    ],
  },
];

export default function PrivacyPage() {
  return (
    <V2Layout footer="compact">
      <div className="mx-auto w-full max-w-page px-5 py-10 md:px-8 md:py-12 lg:px-12">
        <div className="max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-healia-brand">
            Privacy
          </p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-healia-text md:text-4xl">
            How Healia handles your information
          </h1>
          <p className="mt-4 text-base leading-relaxed text-healia-text-secondary md:text-lg">
            We keep privacy simple: your consultations belong to your account,
            and we use your information to deliver guidance — not to advertise
            with it.
          </p>
          <p className="mt-3 text-xs text-healia-text-muted">
            Last updated: March 2026
          </p>
        </div>

        <div className="mt-10 max-w-3xl space-y-0 border-t border-healia-border-subtle">
          {sections.map((section) => (
            <section
              key={section.title}
              className="border-b border-healia-border-subtle py-7"
            >
              <h2 className="text-base font-semibold text-healia-text">
                {section.title}
              </h2>
              <ul className="mt-3 space-y-2.5">
                {section.body.map((line) => (
                  <li
                    key={line}
                    className="flex gap-2.5 text-sm leading-relaxed text-healia-text-secondary md:text-[15px]"
                  >
                    <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-healia-brand" />
                    <span>{line}</span>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>

        <div className="mt-10 flex flex-col gap-3 sm:flex-row">
          <V2Button to="/consultation">Start Consultation</V2Button>
          <V2Button to="/about" variant="secondary">
            About Healia
          </V2Button>
        </div>
      </div>
    </V2Layout>
  );
}
