import { API_URL } from "@/v2/lib/api";
import type {
  AuthSession,
  AuthUser,
  LoginCredentials,
  SignupCredentials,
  SignupResponse,
} from "@/v2/types/auth";

async function parseError(res: Response): Promise<string> {
  try {
    const data = (await res.json()) as { detail?: string | { msg?: string }[] };
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail) && data.detail[0]?.msg) {
      return data.detail[0].msg;
    }
  } catch {
    /* ignore */
  }
  return res.statusText || "Request failed";
}

function isSessionResponse(data: SignupResponse): data is AuthSession {
  return "access_token" in data && Boolean(data.access_token);
}

export async function loginRequest(
  credentials: LoginCredentials,
): Promise<AuthSession> {
  const res = await fetch(`${API_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(credentials),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<AuthSession>;
}

export async function signupRequest(
  credentials: SignupCredentials,
): Promise<SignupResponse> {
  const res = await fetch(`${API_URL}/api/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(credentials),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<SignupResponse>;
}

export async function refreshRequest(refreshToken: string): Promise<AuthSession> {
  const res = await fetch(`${API_URL}/api/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json() as Promise<AuthSession>;
}

export async function meRequest(accessToken: string): Promise<AuthUser> {
  const res = await fetch(`${API_URL}/api/auth/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!res.ok) throw new Error(await parseError(res));
  const data = (await res.json()) as { user: AuthUser };
  return data.user;
}

export function normalizeSignupResponse(data: SignupResponse): {
  session: AuthSession | null;
  message: string | null;
} {
  if (isSessionResponse(data)) {
    return { session: data, message: null };
  }
  return { session: null, message: data.message };
}
