import { Link } from "react-router-dom";
import { V2Button } from "./V2Button";

export function V2Navigation() {
  return (
    <header className="sticky top-0 z-50 border-b border-healia-border-subtle bg-healia-bg/95 backdrop-blur-sm">
      <div className="mx-auto flex h-16 max-w-page items-center justify-between px-5 md:px-8 lg:px-12">
        <Link
          to="/v2"
          className="flex items-center gap-2.5 text-healia-text transition-opacity hover:opacity-80"
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-healia-brand text-sm font-semibold text-white">
            H
          </span>
          <span className="text-xl font-semibold tracking-tight">Healia</span>
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          <Link
            to="/v2"
            className="text-sm text-healia-text-secondary transition-colors hover:text-healia-text"
          >
            Home
          </Link>
          <Link
            to="/v2/about"
            className="text-sm text-healia-text-secondary transition-colors hover:text-healia-text"
          >
            About
          </Link>
          <Link
            to="/v2/privacy"
            className="text-sm text-healia-text-secondary transition-colors hover:text-healia-text"
          >
            Privacy
          </Link>
        </nav>

        <V2Button to="/v2/consultation" className="px-5 py-2.5 text-sm">
          Start Consultation
        </V2Button>
      </div>
    </header>
  );
}
