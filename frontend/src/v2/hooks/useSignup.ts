import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/v2/context/AuthContext";
import { normalizeSignupResponse, signupRequest } from "@/v2/lib/authApi";
import type { SignupCredentials } from "@/v2/types/auth";

export function useSignup(defaultRedirect = "/consultation") {
  const navigate = useNavigate();
  const { setSession } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);

  const signup = useCallback(
    async (credentials: SignupCredentials, redirectTo?: string) => {
      setIsPending(true);
      setError(null);
      setInfo(null);
      try {
        const data = await signupRequest(credentials);
        const { session, message } = normalizeSignupResponse(data);
        if (session) {
          setSession(session);
          navigate(redirectTo || defaultRedirect, { replace: true });
          return;
        }
        setInfo(message || "Account created. Please log in.");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Signup failed");
      } finally {
        setIsPending(false);
      }
    },
    [defaultRedirect, navigate, setSession],
  );

  return { signup, error, info, isPending, clearMessages: () => { setError(null); setInfo(null); } };
}
