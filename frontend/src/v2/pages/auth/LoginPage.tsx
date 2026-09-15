import { FormEvent, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { AuthField } from "@/v2/components/auth/AuthField";
import { AuthLayout } from "@/v2/components/auth/AuthLayout";
import { V2Button } from "@/v2/components/V2Button";
import { useLogin } from "@/v2/hooks/useLogin";

export default function LoginPage() {
  const [searchParams] = useSearchParams();
  const next = searchParams.get("next") || "/consultation";
  const { login, error, isPending } = useLogin(next);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    void login({ email: email.trim(), password }, next);
  };

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to continue your consultation or view past guidance."
      footer={
        <>
          Don&apos;t have an account?{" "}
          <Link to={`/signup?next=${encodeURIComponent(next)}`} className="font-medium text-healia-brand hover:underline">
            Create one
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
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
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Your password"
        />

        {error ? (
          <p className="rounded-lg border border-healia-danger/20 bg-healia-danger/[0.05] px-3 py-2 text-sm text-healia-danger">
            {error}
          </p>
        ) : null}

        <V2Button
          type="submit"
          disabled={isPending}
          className="w-full px-4 py-2.5 text-sm"
        >
          {isPending ? "Signing in…" : "Sign in"}
        </V2Button>
      </form>
    </AuthLayout>
  );
}
