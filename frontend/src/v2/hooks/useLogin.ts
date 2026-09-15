import { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/v2/context/AuthContext";
import { loginRequest } from "@/v2/lib/authApi";
import type { LoginCredentials } from "@/v2/types/auth";

export function useLogin(defaultRedirect = "/consultation") {
  const navigate = useNavigate();
  const { setSession } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);

  const login = useCallback(
    async (credentials: LoginCredentials, redirectTo?: string) => {
      setIsPending(true);
      setError(null);
      try {
        const session = await loginRequest(credentials);
        setSession(session);
        navigate(redirectTo || defaultRedirect, { replace: true });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Login failed");
      } finally {
        setIsPending(false);
      }
    },
    [defaultRedirect, navigate, setSession],
  );

  return { login, error, isPending, clearError: () => setError(null) };
}
