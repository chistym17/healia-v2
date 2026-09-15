import { Link } from "react-router-dom";
import { V2Button } from "./V2Button";
import { useAuth } from "@/v2/context/AuthContext";

export function V2Navigation() {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <header className="sticky top-0 z-50 border-b border-healia-border-subtle bg-healia-bg/95 backdrop-blur-sm">
      <div className="mx-auto flex h-16 max-w-page items-center justify-between gap-3 px-5 md:px-8 lg:px-12">
        <Link
          to="/"
          className="flex items-center gap-2.5 text-healia-text transition-opacity hover:opacity-80"
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-healia-brand text-sm font-semibold text-white">
            H
          </span>
          <span className="text-xl font-semibold tracking-tight">Healia</span>
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          <Link
            to="/"
            className="text-sm text-healia-text-secondary transition-colors hover:text-healia-text"
          >
            Home
          </Link>
          <Link
            to="/about"
            className="text-sm text-healia-text-secondary transition-colors hover:text-healia-text"
          >
            About
          </Link>
          <Link
            to="/privacy"
            className="text-sm text-healia-text-secondary transition-colors hover:text-healia-text"
          >
            Privacy
          </Link>
        </nav>

        <div className="flex items-center gap-2">
          {isAuthenticated ? (
            <>
              <span className="hidden max-w-[10rem] truncate text-sm text-healia-text-secondary sm:inline">
                {user?.display_name || user?.email}
              </span>
              <V2Button variant="text" onClick={logout} className="px-3 py-2 text-sm">
                Sign out
              </V2Button>
              <V2Button to="/consultations" variant="secondary" className="px-4 py-2.5 text-sm">
                History
              </V2Button>
              <V2Button to="/consultation" className="px-5 py-2.5 text-sm">
                Consultation
              </V2Button>
            </>
          ) : (
            <>
              <V2Button to="/login" variant="secondary" className="px-4 py-2.5 text-sm">
                Sign in
              </V2Button>
              <V2Button to="/signup" className="px-5 py-2.5 text-sm">
                Sign up
              </V2Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
