import { Link } from "react-router-dom";

const links = [
  { label: "About", to: "/about" },
  { label: "Privacy", to: "/privacy" },
  { label: "History", to: "/consultations" },
];

type V2FooterProps = {
  /** Slim bar for app pages; full for marketing homepage */
  variant?: "full" | "compact";
};

export function V2Footer({ variant = "full" }: V2FooterProps) {
  if (variant === "compact") {
    return (
      <footer className="border-t border-healia-border-subtle bg-healia-bg">
        <div className="mx-auto flex max-w-page flex-wrap items-center justify-between gap-2 px-5 py-3 md:px-8 lg:px-12">
          <p className="text-[11px] text-healia-text-muted">
            © {new Date().getFullYear()} Healia · Guidance only, not a diagnosis
          </p>
          <nav className="flex items-center gap-4">
            {links.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className="text-[11px] text-healia-text-muted transition-colors hover:text-healia-brand"
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
      </footer>
    );
  }

  return (
    <footer className="border-t border-healia-border bg-healia-bg-secondary">
      <div className="mx-auto max-w-page px-5 md:px-8 lg:px-12">
        <div className="flex flex-col gap-6 py-8 md:flex-row md:items-start md:justify-between md:py-10">
          <div className="max-w-sm">
            <Link
              to="/"
              className="inline-flex items-center gap-2 text-healia-text transition-opacity hover:opacity-80"
            >
              <span className="flex h-7 w-7 items-center justify-center rounded-md bg-healia-brand text-xs font-semibold text-white">
                H
              </span>
              <span className="font-semibold tracking-tight">Healia</span>
            </Link>
            <p className="mt-3 text-sm leading-relaxed text-healia-text-secondary">
              Calm voice consultations with clear, evidence-based next steps.
            </p>
          </div>
          <nav className="flex flex-wrap gap-x-6 gap-y-2">
            {[
              { label: "Start", to: "/consultation" },
              { label: "History", to: "/consultations" },
              { label: "About", to: "/about" },
              { label: "Privacy", to: "/privacy" },
            ].map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className="text-sm text-healia-text-secondary transition-colors hover:text-healia-brand"
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="border-t border-healia-border py-4">
          <p className="text-xs text-healia-text-muted">
            © {new Date().getFullYear()} Healia · Not medical advice or emergency care
          </p>
        </div>
      </div>
    </footer>
  );
}
