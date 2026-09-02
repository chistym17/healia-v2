import { Link } from "react-router-dom";
import { V2Button } from "./V2Button";

function FooterLogo() {
  return (
    <Link
      to="/v2"
      className="inline-flex items-center gap-2.5 text-healia-text transition-opacity hover:opacity-80"
    >
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-healia-brand text-sm font-semibold text-white">
        H
      </span>
      <span className="text-lg font-semibold tracking-tight">Healia</span>
    </Link>
  );
}

const exploreLinks = [
  { label: "Home", to: "/v2" },
  { label: "Start Consultation", to: "/v2/consultation" },
];

const companyLinks = [
  { label: "About", to: "/v2/about" },
  { label: "Privacy", to: "/v2/privacy" },
];

export function V2Footer() {
  return (
    <footer className="border-t border-healia-border bg-healia-bg-secondary">
      <div className="mx-auto max-w-page px-5 md:px-8 lg:px-12">
        {/* Main footer */}
        <div className="grid gap-10 py-14 md:grid-cols-[1.4fr_1fr_1fr] md:gap-12 lg:py-16">
          <div>
            <FooterLogo />
            <p className="mt-4 max-w-sm text-sm leading-relaxed text-healia-text-secondary">
              A calm health consultation assistant. Describe your symptoms,
              get evidence-based guidance, and know when to seek care.
            </p>
            <div className="mt-6">
              <V2Button to="/v2/consultation" className="px-5 py-2.5 text-sm">
                Start Consultation
              </V2Button>
            </div>
            <p className="mt-6 text-xs text-healia-text-muted">
              Evidence-based · Voice-first · Private consultation
            </p>
          </div>

          <nav aria-label="Explore">
            <p className="text-xs font-semibold uppercase tracking-wider text-healia-text-muted">
              Explore
            </p>
            <ul className="mt-4 space-y-2.5">
              {exploreLinks.map((link) => (
                <li key={link.to}>
                  <Link
                    to={link.to}
                    className="text-sm text-healia-text-secondary transition-colors hover:text-healia-brand"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          <nav aria-label="Company">
            <p className="text-xs font-semibold uppercase tracking-wider text-healia-text-muted">
              Company
            </p>
            <ul className="mt-4 space-y-2.5">
              {companyLinks.map((link) => (
                <li key={link.to}>
                  <Link
                    to={link.to}
                    className="text-sm text-healia-text-secondary transition-colors hover:text-healia-brand"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        {/* Bottom bar */}
        <div className="flex flex-col gap-3 border-t border-healia-border py-6 md:flex-row md:items-center md:justify-between">
          <p className="text-xs text-healia-text-muted">
            &copy; {new Date().getFullYear()} Healia. All rights reserved.
          </p>
          <p className="max-w-lg text-xs leading-relaxed text-healia-text-muted md:text-right">
            General health guidance only — not medical advice, diagnosis, or
            emergency care.
          </p>
        </div>
      </div>
    </footer>
  );
}
