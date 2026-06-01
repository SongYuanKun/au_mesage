const TOKEN_KEY = "au_auth_token";

export function getAuthToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setAuthToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearAuthToken(): void {
  sessionStorage.removeItem(TOKEN_KEY);
}

export function isAuthRequired(): boolean {
  return import.meta.env.VITE_AUTH_ENABLED === "true";
}
