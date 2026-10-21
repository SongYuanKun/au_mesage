const TOKEN_KEY = "au_auth_token";

declare global {
  interface Window {
    __AU_RUNTIME_CONFIG__?: {
      authEnabled?: boolean;
    };
  }
}

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
  // Docker serves this SPA through Flask.  The preceding runtime-config script
  // comes from that same Flask process, avoiding a build-time auth setting that
  // can drift from AUTH_ENABLED at container startup.
  return window.__AU_RUNTIME_CONFIG__?.authEnabled === true;
}
