import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";

export default function Login() {
  const { login, authRequired } = useAuth();
  const navigate = useNavigate();
  const [token, setToken] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (!authRequired) {
    return (
      <div className="mx-auto max-w-md p-8 text-center">
        <p>当前环境未启用认证（VITE_AUTH_ENABLED≠true）。</p>
        <button
          type="button"
          className="mt-4 text-blue-600 underline"
          onClick={() => navigate("/")}
        >
          返回首页
        </button>
      </div>
    );
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(token.trim());
      navigate("/admin/sources");
    } catch {
      setError("Token 无效或后端拒绝，请检查后重试");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-[60vh] max-w-md flex-col justify-center p-6">
      <h1 className="mb-2 text-2xl font-semibold">管理端登录</h1>
      <p className="mb-6 text-sm text-gray-600">
        请输入运维下发的 Bearer Token（与后端 AUTH_ADMIN_TOKEN / AUTH_OPS_TOKEN 对应）。
      </p>
      <form onSubmit={onSubmit} className="space-y-4">
        <label className="block text-sm font-medium">
          API Token
          <input
            type="password"
            className="mt-1 w-full rounded border px-3 py-2"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            autoComplete="off"
            required
          />
        </label>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded bg-amber-600 py-2 text-white disabled:opacity-50"
        >
          {submitting ? "验证中…" : "登录"}
        </button>
      </form>
    </div>
  );
}
