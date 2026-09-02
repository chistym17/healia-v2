import { Link } from "react-router-dom";

export function V2Footer() {
  return (
    <footer className="border-t border-healia-border bg-healia-bg">
      <div className="mx-auto max-w-page px-5 py-12 md:px-8 lg:px-12">
        <div className="flex flex-col gap-8 md:flex-row md:items-start md:justify-between">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="flex h-7 w-7 items-center justify-center rounded-md bg-healia-brand text-xs font-semibold text-white">
                H
              </span>
              <span className="font-semibold text-healia-text">Healia</span>
            </div>
            <p className="mt-3 max-w-xs text-sm leading-relaxed text-healia-text-secondary">
              A calm health consultation assistant for when you need clarity
              about your symptoms.
            </p>
          </div>

          <nav className="flex gap-10">
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-healia-text-muted">
                Product
              </p>
              <ul className="mt-3 space-y-2">
                <li>
                  <Link
                    to="/v2/consultation"
                    className="text-sm text-healia-text-secondary transition-colors hover:text-healia-text"
                  >
                    Start Consultation
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-healia-text-muted">
                Company
              </p>
              <ul className="mt-3 space-y-2">
                <li>
                  <Link
                    to="/v2/about"
                    className="text-sm text-healia-text-secondary transition-colors hover:text-healia-text"
                  >
                    About
                  </Link>
                </li>
                <li>
                  <Link
                    to="/v2/privacy"
                    className="text-sm text-healia-text-secondary transition-colors hover:text-healia-text"
                  >
                    Privacy
                  </Link>
                </li>
              </ul>
            </div>
          </nav>
        </div>

        <p className="mt-10 border-t border-healia-border-subtle pt-8 text-xs leading-relaxed text-healia-text-muted">
          Healia provides general health guidance and does not replace care
          from a qualified healthcare professional. If you have a medical
          emergency, call your local emergency number immediately.
        </p>
      </div>
    </footer>
  );
}
