export type AuthUser = {
  id: string;
  email: string;
  display_name: string | null;
};

export type AuthSession = {
  access_token: string;
  refresh_token: string;
  expires_in?: number;
  token_type?: string;
  user: AuthUser;
};

export type SignupResponse = AuthSession | {
  user: AuthUser;
  session: null;
  message: string;
};

export type LoginCredentials = {
  email: string;
  password: string;
};

export type SignupCredentials = LoginCredentials & {
  display_name?: string;
  turnstile_token?: string;
};
