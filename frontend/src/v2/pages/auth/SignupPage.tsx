import { FormEvent, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Turnstile, type TurnstileInstance } from "@marsidev/react-turnstile";
import { AuthField } from "@/v2/components/auth/AuthField";
import { AuthLayout } from "@/v2/components/auth/AuthLayout";
import { V2Button } from "@/v2/components/V2Button";
import { useSignup } from "@/v2/hooks/useSignup";

const TURNSTILE_SITE_KEY =
  (import.meta.env.VITE_TURNSTILE_SITE_KEY as string | undefined)?.trim() || "";

export default function SignupPage() {
  const [searchParams] = useSearchParams();
  const next = searchParams.get("next") || "/consultation";
  const { signup, error, info, isPending } = useSignup(next);
  const turnstileRef = useRef<TurnstileInstance | null>(null);

  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);

  const botCheckReady = !TURNSTILE_SITE_KEY || Boolean(turnstileToken);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!botCheckReady) return;
    try {
      await signup(
        {
          email: email.trim(),
          password,
          display_name: displayName.trim() || undefined,
          turnstile_token: turnstileToken || undefined,
        },
        next,
      );
    } finally {
      // Tokens are single-use; refresh for another attempt.
      turnstileRef.current?.reset();
      setTurnstileToken(null);
    }
  };

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Save consultations and come back to your guidance anytime."
      footer={
        <>
          Already have an account?{" "}
          <Link
            to={`/login?next=${encodeURIComponent(next)}`}
            className="font-medium text-healia-brand hover:underline"
          >
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <AuthField
          label="Name (optional)"
          name="display_name"
          autoComplete="name"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          placeholder="How should we address you?"
        />
        <AuthField
          label="Email"
          name="email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
        />
        <AuthField
          label="Password"
          name="password"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="At least 8 characters"
          hint="Use at least 8 characters."
        />

        {TURNSTILE_SITE_KEY ? (
          <div className="space-y-1.5">
            <p className="text-sm font-medium text-healia-text">
              Security check
            </p>
            <div className="flex min-h-[65px] items-center justify-start overflow-hidden rounded-lg border border-healia-border bg-healia-bg px-2 py-2">
              <Turnstile
                ref={turnstileRef}
                siteKey={TURNSTILE_SITE_KEY}
                options={{
                  theme: "light",
                  size: "normal",
                  appearance: "always",
                }}
                onSuccess={setTurnstileToken}
                onExpire={() => setTurnstileToken(null)}
                onError={() => setTurnstileToken(null)}
              />
            </div>
            <p className="text-xs text-healia-text-muted">
              Confirms you’re human — usually finishes on its own.
            </p>
          </div>
        ) : null}

        {error ? (
          <p className="rounded-lg border border-healia-danger/20 bg-healia-danger/[0.05] px-3 py-2 text-sm text-healia-danger">
            {error}
          </p>
        ) : null}

        {info ? (
          <p className="rounded-lg border border-healia-brand/20 bg-healia-brand-light/50 px-3 py-2 text-sm text-healia-text-secondary">
            {info}{" "}
            <Link
              to={`/login?next=${encodeURIComponent(next)}`}
              className="font-medium text-healia-brand hover:underline"
            >
              Sign in
            </Link>
          </p>
        ) : null}

        <V2Button
          type="submit"
          disabled={isPending || !botCheckReady}
          className="w-full px-4 py-2.5 text-sm"
        >
          {isPending
            ? "Creating account…"
            : !botCheckReady
              ? "Verifying…"
              : "Create account"}
        </V2Button>
      </form>
    </AuthLayout>
  );
}
