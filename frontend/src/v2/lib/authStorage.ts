import type { AuthSession, AuthUser } from "@/v2/types/auth";

const STORAGE_KEY = "healia_auth";

export type StoredAuth = {
  accessToken: string;
  refreshToken: string;
  user: AuthUser;
};

export function loadStoredAuth(): StoredAuth | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as StoredAuth;
    if (!parsed.accessToken || !parsed.user?.id) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function saveStoredAuth(session: AuthSession): StoredAuth {
  const stored: StoredAuth = {
    accessToken: session.access_token,
    refreshToken: session.refresh_token,
    user: session.user,
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
  return stored;
}

export function clearStoredAuth(): void {
  localStorage.removeItem(STORAGE_KEY);
}

export function getAccessToken(): string | null {
  return loadStoredAuth()?.accessToken ?? null;
}
