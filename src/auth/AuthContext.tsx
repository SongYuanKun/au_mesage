import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import axios from "axios";
import {
  clearAuthToken,
  getAuthToken,
  isAuthRequired,
  setAuthToken,
} from "@/auth/tokenStorage";

export type AuthRole = "admin" | "ops" | "user" | "guest" | null;

interface AuthState {
  token: string | null;
  role: AuthRole;
  loading: boolean;
  authRequired: boolean;
  login: (token: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getAuthToken());
  const [role, setRole] = useState<AuthRole>(null);
  const [loading, setLoading] = useState(isAuthRequired());
  const authRequired = isAuthRequired();

  const refreshSession = useCallback(async (activeToken: string) => {
    const res = await axios.post(
      "/api/auth/session",
      {},
      { headers: { Authorization: `Bearer ${activeToken}` } }
    );
    setRole((res.data?.data?.role as AuthRole) ?? null);
  }, []);

  useEffect(() => {
    if (!authRequired) {
      setRole("guest");
      setLoading(false);
      return;
    }
    if (!token) {
      setRole(null);
      setLoading(false);
      return;
    }
    refreshSession(token)
      .catch(() => {
        clearAuthToken();
        setToken(null);
        setRole(null);
      })
      .finally(() => setLoading(false));
  }, [authRequired, token, refreshSession]);

  const login = useCallback(
    async (nextToken: string) => {
      setAuthToken(nextToken);
      setToken(nextToken);
      await refreshSession(nextToken);
    },
    [refreshSession]
  );

  const logout = useCallback(async () => {
    const current = getAuthToken();
    if (current) {
      try {
        await axios.post(
          "/api/auth/logout",
          {},
          { headers: { Authorization: `Bearer ${current}` } }
        );
      } catch {
        /* ignore */
      }
    }
    clearAuthToken();
    setToken(null);
    setRole(null);
  }, []);

  const value = useMemo(
    () => ({
      token,
      role,
      loading,
      authRequired,
      login,
      logout,
    }),
    [token, role, loading, authRequired, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}

export function ProtectedRoute({
  children,
  roles,
}: {
  children: ReactNode;
  roles?: AuthRole[];
}) {
  const { authRequired, role, loading, token } = useAuth();
  if (!authRequired) {
    return <>{children}</>;
  }
  if (loading) {
    return <p className="p-6 text-center text-gray-500">正在验证登录状态…</p>;
  }
  if (!token || !role) {
    window.location.href = "/login";
    return null;
  }
  if (roles && !roles.includes(role)) {
    return (
      <p className="p-6 text-center text-red-600">无权限访问该页面（需要 {roles.join(" / ")}）</p>
    );
  }
  return <>{children}</>;
}
