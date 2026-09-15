import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  meRequest,
  refreshRequest,
} from "@/v2/lib/authApi";
import {
  clearStoredAuth,
  loadStoredAuth,
  saveStoredAuth,
  type StoredAuth,
} from "@/v2/lib/authStorage";
import type { AuthSession, AuthUser } from "@/v2/types/auth";

type AuthContextValue = {
  user: AuthUser | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setSession: (session: AuthSession) => void;
  logout: () => void;
  refreshProfile: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [stored, setStored] = useState<StoredAuth | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const setSession = useCallback((session: AuthSession) => {
    const next = saveStoredAuth(session);
    setStored(next);
  }, []);

  const logout = useCallback(() => {
    clearStoredAuth();
    setStored(null);
  }, []);

  const refreshProfile = useCallback(async () => {
    if (!stored?.accessToken) return;
    const user = await meRequest(stored.accessToken);
    setStored((prev) => (prev ? { ...prev, user } : prev));
  }, [stored?.accessToken]);

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      const local = loadStoredAuth();
      if (!local) {
        if (!cancelled) setIsLoading(false);
        return;
      }

      try {
        const user = await meRequest(local.accessToken);
        if (!cancelled) {
          setStored({ ...local, user });
        }
      } catch {
        try {
          const session = await refreshRequest(local.refreshToken);
          const next = saveStoredAuth(session);
          if (!cancelled) setStored(next);
        } catch {
          clearStoredAuth();
          if (!cancelled) setStored(null);
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user: stored?.user ?? null,
      accessToken: stored?.accessToken ?? null,
      isAuthenticated: Boolean(stored?.accessToken),
      isLoading,
      setSession,
      logout,
      refreshProfile,
    }),
    [stored, isLoading, setSession, logout, refreshProfile],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
