import { useState, useEffect, useCallback, useRef } from "react";
import { Bell, BellRing, Wifi, WifiOff, RefreshCw, CheckCircle, XCircle } from "lucide-react";
import AppLayout from "@/components/layout/AppLayout";
import { useSSEAlert } from "@/hooks/useSSEAlert";
import { fetchAlertChannels, type AlertChannel } from "@/api/price";
import usePriceStore from "@/stores/priceStore";

/** 品类选项 */
type DataTypeOption = "黄金" | "白银";

/** 方向选项 */
type DirectionOption = "gte" | "lte";

const DATA_TYPE_LABELS: Record<DataTypeOption, string> = {
  "黄金": "🥇 黄金",
  "白银": "🥈 白银",
};

const DIRECTION_LABELS: Record<DirectionOption, string> = {
  gte: "价格上涨到",
  lte: "价格下跌到",
};

/** Toast 通知项 */
interface Toast {
  id: number;
  message: string;
  type: "alert" | "price" | "info" | "error";
  timestamp: number;
}

let toastIdCounter = 0;

export default function Alerts() {
  const [alertDataType, setAlertDataType] = useState<DataTypeOption>("黄金");
  const [alertTarget, setAlertTarget] = useState<string>("");
  const [alertDirection, setAlertDirection] = useState<DirectionOption>("gte");

  // ===== SSE 连接状态 =====
  const [sseConnected, setSseConnected] = useState(false);
  const [currentPrice, setCurrentPrice] = useState<{ gold: number | null; silver: number | null }>({
    gold: null,
    silver: null,
  });

  // ===== Toast 通知 =====
  const [toasts, setToasts] = useState<Toast[]>([]);

  // ===== 渠道状态 =====
  const [channels, setChannels] = useState<AlertChannel[]>([]);
  const [channelsLoading, setChannelsLoading] = useState(false);
  const [channelsError, setChannelsError] = useState<string | null>(null);

  // ===== Store 数据 =====
  const { goldPrice, silverPrice } = usePriceStore();

  // 请求浏览器通知权限
  const notificationPermissionRef = useRef<NotificationPermission>("default");
  useEffect(() => {
    if ("Notification" in window) {
      notificationPermissionRef.current = Notification.permission;
    }
  }, []);

  // 获取已配置渠道
  const loadChannels = useCallback(async () => {
    setChannelsLoading(true);
    setChannelsError(null);
    try {
      const data = await fetchAlertChannels();
      setChannels(data);
    } catch (err) {
      setChannelsError(err instanceof Error ? err.message : "获取渠道失败");
    } finally {
      setChannelsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadChannels();
  }, [loadChannels]);

  // 更新当前价格
  useEffect(() => {
    if (goldPrice) {
      setCurrentPrice((prev) => ({ ...prev, gold: goldPrice.real_time_price }));
    }
    if (silverPrice) {
      setCurrentPrice((prev) => ({ ...prev, silver: silverPrice.real_time_price }));
    }
  }, [goldPrice, silverPrice]);

  // 添加 Toast 通知
  const addToast = useCallback((message: string, type: Toast["type"]) => {
    const id = ++toastIdCounter;
    setToasts((prev) => [...prev, { id, message, type, timestamp: Date.now() }]);
    // 自动移除
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  }, []);

  // SSE 事件回调
  const handleSSEConnect = useCallback(() => {
    setSseConnected(true);
    addToast("SSE 连接已建立", "info");
  }, [addToast]);

  const handleSSEDisconnect = useCallback(() => {
    setSseConnected(false);
  }, []);

  const handlePriceUpdate = useCallback((data: { gold?: number; silver?: number; data_type?: string; price?: number }) => {
    // 更新实时价格显示
    if (data.gold !== undefined) {
      setCurrentPrice((prev) => ({ ...prev, gold: data.gold ?? prev.gold }));
    }
    if (data.silver !== undefined) {
      setCurrentPrice((prev) => ({ ...prev, silver: data.silver ?? prev.silver }));
    }
    if (data.data_type && data.price !== undefined) {
      addToast(`${data.data_type} 实时价格：¥${data.price.toFixed(2)}`, "price");
    }
  }, [addToast]);

  const handleAlertTriggered = useCallback((data: { message?: string; data_type?: string; target?: number; direction?: string }) => {
    const msg = data.message || `提醒触发：${data.data_type || ""} ${data.direction === "gte" ? "≥" : "≤"} ${data.target || ""}`;
    addToast(msg, "alert");

    // 浏览器通知
    if ("Notification" in window && Notification.permission === "granted") {
      new Notification("价格提醒", {
        body: msg,
        icon: "/favicon.svg",
      });
    }
  }, [addToast]);

  const handleSSEError = useCallback((data: { message?: string }) => {
    const msg = data.message || "SSE 连接异常";
    addToast(msg, "error");
  }, [addToast]);

  const handlePing = useCallback(() => {
    // 心跳，不显示 toast
  }, []);

  // 启动 SSE 订阅
  const { connect, disconnect, isConnected } = useSSEAlert({
    onConnect: handleSSEConnect,
    onDisconnect: handleSSEDisconnect,
    onPrice: handlePriceUpdate,
    onAlert: handleAlertTriggered,
    onError: handleSSEError,
    onPing: handlePing,
  });

  // 开始订阅
  const handleSubscribe = useCallback(() => {
    // 请求通知权限
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission().then((perm) => {
        notificationPermissionRef.current = perm;
      });
    }
    connect(alertDataType, parseFloat(alertTarget), alertDirection);
  }, [connect, alertDataType, alertTarget, alertDirection]);

  // 取消订阅
  const handleUnsubscribe = useCallback(() => {
    disconnect();
    addToast("已断开订阅", "info");
  }, [disconnect, addToast]);

  // 关闭 Toast
  const removeToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const connected = isConnected || sseConnected;

  return (
    <AppLayout
      hero={{
        eyebrow: "Alerts",
        title: "价格提醒",
        subtitle: "设置目标价并接收浏览器推送通知。",
      }}
    >

        {/* Toast 通知容器 */}
        {toasts.length > 0 && (
          <div className="fixed top-20 right-4 z-[100] space-y-2 max-w-sm">
            {toasts.map((toast) => (
              <div
                key={toast.id}
                className={`px-4 py-3 rounded-xl shadow-lg border text-sm flex items-start justify-between gap-2 animate-slide-in-right ${
                  toast.type === "alert"
                    ? "bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800 text-yellow-800 dark:text-yellow-300"
                    : toast.type === "price"
                    ? "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-800 dark:text-blue-300"
                    : toast.type === "error"
                    ? "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-800 dark:text-red-300"
                    : "bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300"
                }`}
              >
                <span>{toast.message}</span>
                <button
                  onClick={() => removeToast(toast.id)}
                  className="flex-shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}

        {/* 实时价格显示面板 */}
        <div className="rounded-2xl shadow-lg border border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 flex items-center gap-2">
              {connected ? (
                <Wifi className="w-5 h-5 text-green-500" />
              ) : (
                <WifiOff className="w-5 h-5 text-gray-400" />
              )}
              实时价格
            </h3>
            <span
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${
                connected
                  ? "bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400"
                  : "bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400"
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${connected ? "bg-green-500 animate-pulse" : "bg-gray-400"}`} />
              {connected ? "已连接" : "未连接"}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">🥇 黄金</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {currentPrice.gold !== null ? `¥${currentPrice.gold.toFixed(2)}` : "--"}
              </p>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">🥈 白银</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {currentPrice.silver !== null ? `¥${currentPrice.silver.toFixed(2)}` : "--"}
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* 创建提醒表单 */}
          <div className="rounded-2xl shadow-lg border border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 p-6">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4 flex items-center gap-2">
              <BellRing className="w-5 h-5" />
              创建价格提醒
            </h3>

            {/* 品类选择 */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                品类
              </label>
              <div className="flex gap-2">
                {(["黄金", "白银"] as DataTypeOption[]).map((dt) => (
                  <button
                    key={dt}
                    onClick={() => setAlertDataType(dt)}
                    className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      alertDataType === dt
                        ? "bg-blue-600 text-white"
                        : "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                    }`}
                  >
                    {DATA_TYPE_LABELS[dt]}
                  </button>
                ))}
              </div>
            </div>

            {/* 方向选择 */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                提醒方向
              </label>
              <div className="flex gap-2">
                {(["gte", "lte"] as DirectionOption[]).map((dir) => (
                  <button
                    key={dir}
                    onClick={() => setAlertDirection(dir)}
                    className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      alertDirection === dir
                        ? "bg-blue-600 text-white"
                        : "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                    }`}
                  >
                    {DIRECTION_LABELS[dir]}
                  </button>
                ))}
              </div>
            </div>

            {/* 目标价格 */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                目标价格（元/克）
              </label>
              <input
                type="number"
                value={alertTarget}
                onChange={(e) => setAlertTarget(e.target.value)}
                placeholder="例如：600"
                className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-colors"
              />
            </div>

            {/* 订阅 / 取消按钮 */}
            <div className="flex gap-3">
              <button
                onClick={handleSubscribe}
                disabled={!alertTarget || parseFloat(alertTarget) <= 0}
                className="flex-1 px-4 py-2.5 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <Bell className="w-4 h-4" />
                开始订阅
              </button>
              <button
                onClick={handleUnsubscribe}
                disabled={!connected}
                className="px-4 py-2.5 rounded-lg bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                取消订阅
              </button>
            </div>
          </div>

          {/* 已配置推送渠道 */}
          <div className="rounded-2xl shadow-lg border border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 flex items-center gap-2">
                <CheckCircle className="w-5 h-5" />
                推送渠道
              </h3>
              <button
                onClick={loadChannels}
                className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-gray-500 dark:text-gray-400"
                aria-label="刷新渠道"
              >
                <RefreshCw className={`w-4 h-4 ${channelsLoading ? "animate-spin" : ""}`} />
              </button>
            </div>

            {channelsError && (
              <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm">
                ⚠️ {channelsError}
              </div>
            )}

            {channelsLoading ? (
              <div className="space-y-3 animate-pulse">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-16 bg-gray-100 dark:bg-gray-700 rounded-lg" />
                ))}
              </div>
            ) : channels.length === 0 ? (
              <div className="text-center py-8 text-gray-400 dark:text-gray-500">
                <XCircle className="w-12 h-12 mx-auto mb-2 opacity-40" />
                <p className="text-sm">暂无已配置的推送渠道</p>
                <p className="text-xs mt-1">请先在后台配置推送渠道</p>
              </div>
            ) : (
              <div className="space-y-3">
                {channels.map((channel, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50"
                  >
                    <div>
                      <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                        {channel.name || channel.type || `渠道 ${index + 1}`}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {channel.type || "未知类型"}
                        {channel.status ? ` · ${channel.status}` : ""}
                      </p>
                    </div>
                    <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                      <CheckCircle className="w-3 h-3" />
                      已配置
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 浏览器通知权限提示 */}
        {"Notification" in window && Notification.permission !== "granted" && (
          <div className="rounded-2xl shadow-lg border border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-900/20 p-4 mb-8">
            <p className="text-sm text-yellow-800 dark:text-yellow-300">
              💡 提示：当前浏览器通知权限为"{Notification.permission}"，开启后可在价格触发时收到桌面通知。
            </p>
          </div>
        )}

        {/* Footer */}
    </AppLayout>
  );
}
