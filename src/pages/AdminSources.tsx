import { useCallback, useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import { useAuth } from "@/auth/AuthContext";
import { getAuthToken } from "@/auth/tokenStorage";
import axios from "axios";

interface SourceRow {
  source_id: string;
  enabled: boolean;
  priority: number;
  updated_at?: string;
  health?: {
    last_success_at?: string | null;
    last_failure_at?: string | null;
    failure_count?: number;
    last_latency_ms?: number | null;
  };
}

function authHeaders() {
  const token = getAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export default function AdminSources() {
  const { role } = useAuth();
  const [rows, setRows] = useState<SourceRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const res = await axios.get<{ success: boolean; data: SourceRow[] }>(
        "/api/admin/sources",
        { headers: authHeaders() }
      );
      setRows(res.data.data ?? []);
    } catch {
      setError("加载数据源配置失败");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function save(row: SourceRow) {
    setSaving(row.source_id);
    try {
      await axios.put(
        `/api/admin/sources/${row.source_id}`,
        { enabled: row.enabled, priority: row.priority },
        { headers: authHeaders() }
      );
      await load();
    } catch {
      setError(`保存 ${row.source_id} 失败`);
    } finally {
      setSaving(null);
    }
  }

  async function rollback(sourceId: string) {
    setSaving(sourceId);
    try {
      await axios.post(
        `/api/admin/sources/${sourceId}/rollback`,
        {},
        { headers: authHeaders() }
      );
      await load();
    } catch {
      setError(`回滚 ${sourceId} 失败`);
    } finally {
      setSaving(null);
    }
  }

  const canEdit = role === "admin";

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navbar />
      <main className="mx-auto max-w-4xl p-6">
        <h1 className="mb-2 text-2xl font-semibold">数据源配置</h1>
        <p className="mb-6 text-sm text-gray-600 dark:text-gray-400">
          修改后约 60 秒内采集器按新配置生效；误操作可使用回滚。
        </p>
        {error && <p className="mb-4 text-red-600">{error}</p>}
        <div className="overflow-x-auto rounded-lg border bg-white shadow dark:bg-gray-800">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b bg-gray-100 dark:bg-gray-700">
              <tr>
                <th className="p-3">数据源</th>
                <th className="p-3">启用</th>
                <th className="p-3">优先级</th>
                <th className="p-3">最近成功</th>
                <th className="p-3">失败次数</th>
                <th className="p-3">操作</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, idx) => (
                <tr key={row.source_id} className="border-b">
                  <td className="p-3 font-mono">{row.source_id}</td>
                  <td className="p-3">
                    <input
                      type="checkbox"
                      checked={row.enabled}
                      disabled={!canEdit}
                      onChange={(e) => {
                        const next = [...rows];
                        next[idx] = { ...row, enabled: e.target.checked };
                        setRows(next);
                      }}
                    />
                  </td>
                  <td className="p-3">
                    <input
                      type="number"
                      className="w-20 rounded border px-2 py-1"
                      value={row.priority}
                      disabled={!canEdit}
                      onChange={(e) => {
                        const next = [...rows];
                        next[idx] = { ...row, priority: Number(e.target.value) };
                        setRows(next);
                      }}
                    />
                  </td>
                  <td className="p-3 text-xs">
                    {row.health?.last_success_at ?? "—"}
                  </td>
                  <td className="p-3">{row.health?.failure_count ?? 0}</td>
                  <td className="p-3 space-x-2">
                    {canEdit && (
                      <>
                        <button
                          type="button"
                          className="text-amber-700 underline disabled:opacity-50"
                          disabled={saving === row.source_id}
                          onClick={() => void save(row)}
                        >
                          保存
                        </button>
                        <button
                          type="button"
                          className="text-gray-600 underline disabled:opacity-50"
                          disabled={saving === row.source_id}
                          onClick={() => void rollback(row.source_id)}
                        >
                          回滚
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
