import { useRef, useCallback, useEffect, useState } from "react";

/** SSE 事件回调接口 */
interface SSEAlertCallbacks {
  onConnect?: () => void;
  onDisconnect?: () => void;
  onPrice?: (data: { gold?: number; silver?: number; data_type?: string; price?: number }) => void;
  onAlert?: (data: { message?: string; data_type?: string; target?: number; direction?: string }) => void;
  onError?: (data: { message?: string }) => void;
  onPing?: () => void;
}

/** SSE 连接参数 */
interface SSEAlertOptions extends SSEAlertCallbacks {
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

/**
 * 自定义 Hook：管理 SSE 价格提醒订阅
 *
 * 负责创建 EventSource 连接、监听事件、自动重连。
 */
export function useSSEAlert(options: SSEAlertOptions = {}) {
  const {
    onConnect,
    onDisconnect,
    onPrice,
    onAlert,
    onError,
    onPing,
    reconnectInterval = 5000,
    maxReconnectAttempts = 10,
  } = options;

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const mountedRef = useRef(true);
  const [isConnected, setIsConnected] = useState(false);

  // 清理连接
  const cleanup = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (mountedRef.current) {
      setIsConnected(false);
    }
  }, []);

  // 连接 SSE
  const connect = useCallback(
    (dataType: string, target: number, direction: string) => {
      // 先清理旧连接
      cleanup();
      reconnectAttemptsRef.current = 0;

      const params = new URLSearchParams({
        data_type: dataType,
        target: String(target),
        op: direction,
      });
      const url = `/api/price-alert/subscribe?${params.toString()}`;

      const es = new EventSource(url);
      eventSourceRef.current = es;

      es.onopen = () => {
        if (!mountedRef.current) return;
        reconnectAttemptsRef.current = 0;
        setIsConnected(true);
        onConnect?.();
      };

      es.addEventListener("price", (event) => {
        if (!mountedRef.current) return;
        try {
          const data = JSON.parse(event.data);
          onPrice?.(data);
        } catch {
          // 忽略解析错误
        }
      });

      es.addEventListener("alert", (event) => {
        if (!mountedRef.current) return;
        try {
          const data = JSON.parse(event.data);
          onAlert?.(data);
        } catch {
          // 忽略解析错误
        }
      });

      es.addEventListener("ping", () => {
        if (!mountedRef.current) return;
        onPing?.();
      });

      es.addEventListener("timeout", () => {
        if (!mountedRef.current) return;
        onError?.({ message: "SSE 连接超时" });
      });

      es.addEventListener("error", () => {
        if (!mountedRef.current) return;
        const wasConnected = es.readyState === EventSource.OPEN;
        setIsConnected(false);

        if (wasConnected) {
          onDisconnect?.();
        }

        // 尝试重连
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          reconnectTimerRef.current = setTimeout(() => {
            if (mountedRef.current && reconnectAttemptsRef.current <= maxReconnectAttempts) {
              es.close();
              const newEs = new EventSource(url);
              eventSourceRef.current = newEs;

              // 重新绑定事件
              newEs.onopen = () => {
                if (!mountedRef.current) return;
                reconnectAttemptsRef.current = 0;
                setIsConnected(true);
                onConnect?.();
              };

              newEs.addEventListener("price", (evt) => {
                if (!mountedRef.current) return;
                try {
                  onPrice?.(JSON.parse(evt.data));
                } catch { /* ignore */ }
              });

              newEs.addEventListener("alert", (evt) => {
                if (!mountedRef.current) return;
                try {
                  onAlert?.(JSON.parse(evt.data));
                } catch { /* ignore */ }
              });

              newEs.addEventListener("ping", () => {
                if (!mountedRef.current) return;
                onPing?.();
              });

              newEs.addEventListener("timeout", () => {
                if (!mountedRef.current) return;
                onError?.({ message: "SSE 连接超时" });
              });

              newEs.onerror = () => {
                if (!mountedRef.current) return;
                setIsConnected(false);
              };
            }
          }, reconnectInterval);
        } else {
          onError?.({ message: "SSE 重连次数已达上限" });
        }
      });
    },
    [cleanup, onConnect, onDisconnect, onPrice, onAlert, onError, onPing, reconnectInterval, maxReconnectAttempts]
  );

  // 断开连接
  const disconnect = useCallback(() => {
    cleanup();
    onDisconnect?.();
  }, [cleanup, onDisconnect]);

  // 组件卸载时清理
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      cleanup();
    };
  }, [cleanup]);

  return {
    connect,
    disconnect,
    isConnected,
  };
}

export default useSSEAlert;
