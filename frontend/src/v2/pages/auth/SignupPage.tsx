import { FormEvent, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { AuthField } from "@/v2/components/auth/AuthField";
import { AuthLayout } from "@/v2/components/auth/AuthLayout";
import { V2Button } from "@/v2/components/V2Button";
import { useSignup } from "@/v2/hooks/useSignup";

export default function SignupPage() {
  const [searchParams] = useSearchParams();
  const next = searchParams.get("next") || "/consultation";
  const { signup, error, info, isPending } = useSignup(next);

  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    void signup(
      {
        email: email.trim(),
        password,
        display_name: displayName.trim() || undefined,
      },
      next,
    );
  };

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Save consultations and come back to your guidance anytime."
      footer={
        <>
          Already have an account?{" "}
          <Link to={`/login?next=${encodeURIComponent(next)}`} className="font-medium text-healia-brand hover:underline">
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

        {error ? (
          <p className="rounded-lg border border-healia-danger/20 bg-healia-danger/[0.05] px-3 py-2 text-sm text-healia-danger">
            {error}
          </p>
        ) : null}

        {info ? (
          <p className="rounded-lg border border-healia-brand/20 bg-healia-brand-light/50 px-3 py-2 text-sm text-healia-text-secondary">
            {info}{" "}
            <Link to={`/login?next=${encodeURIComponent(next)}`} className="font-medium text-healia-brand hover:underline">
              Sign in
            </Link>
          </p>
        ) : null}

        <V2Button
          type="submit"
          disabled={isPending}
          className="w-full px-4 py-2.5 text-sm"
        >
          {isPending ? "Creating account…" : "Create account"}
        </V2Button>
      </form>
    </AuthLayout>
  );
}
