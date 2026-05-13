import axios, { type AxiosError } from "axios";

// --- Axios instance with timeout & baseURL ---
const api = axios.create({
  baseURL: "",
  timeout: 10000,
});

// --- Retry helper ---
interface RetryOptions {
  retries?: number;
  delayMs?: number;
}

async function withRetry<T>(
  fn: () => Promise<T>,
  { retries = 2, delayMs = 1000 }: RetryOptions = {}
): Promise<T> {
  let lastError: unknown;
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      lastError = err;
      const axiosErr = err as AxiosError;
      // Only retry on network errors or 5xx, not on 4xx client errors
      const isRetryable =
        !axiosErr.response || (axiosErr.response.status >= 500);
      if (!isRetryable || attempt === retries) {
        break;
      }
      await new Promise((resolve) => setTimeout(resolve, delayMs * (attempt + 1)));
    }
  }
  throw lastError;
}

// --- Error normalizer ---
function normalizeError(err: unknown): never {
  if (axios.isAxiosError(err)) {
    if (err.code === "ECONNABORTED") {
      throw new Error("请求超时，请稍后重试");
    }
    if (!err.response) {
      throw new Error("网络连接失败，请检查网络后重试");
    }
    throw new Error("服务请求失败，请稍后重试");
  }
  if (err instanceof Error) {
    throw err;
  }
  throw new Error("未知错误");
}

// --- API Response wrapper type ---
export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data: T;
  chart_type?: string;
}

// --- Data types ---
export interface PriceOverviewItem {
  data_type: string;
  recycle_price: number;
  real_time_price: number;
  today_high: number;
  today_low: number;
  change: number;
  change_pct: number;
  updated_at: string;
}

export interface CandlestickData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface LineData {
  time: string;
  price: number;
}

export interface RatioData {
  date: string;
  ratio: number;
}

export interface Last7DaysData {
  date: string;
  price: number;
}

export interface PriceTrendResult {
  chart_type: string;
  data: CandlestickData[] | LineData[];
}

// --- API functions with retry & error handling ---

export async function fetchPriceOverview(): Promise<PriceOverviewItem[]> {
  try {
    return await withRetry(async () => {
      const res = await api.get<ApiResponse<PriceOverviewItem[]>>("/api/price-overview");
      if (res.data.success) {
        return res.data.data;
      }
      throw new Error(res.data.message || "获取价格概览失败");
    });
  } catch (err) {
    normalizeError(err);
  }
}

export async function fetchPriceTrend(
  dataType: string,
  range: string
): Promise<PriceTrendResult> {
  try {
    return await withRetry(async () => {
      const res = await api.get<ApiResponse<CandlestickData[] | LineData[]>>("/api/price-trend", {
        params: { data_type: dataType, range },
      });
      if (res.data.success) {
        return { chart_type: res.data.chart_type || "line", data: res.data.data };
      }
      throw new Error(res.data.message || "获取价格趋势失败");
    });
  } catch (err) {
    normalizeError(err);
  }
}

export async function fetchGoldSilverRatio(
  range: string
): Promise<RatioData[]> {
  try {
    return await withRetry(async () => {
      const res = await api.get<ApiResponse<RatioData[]>>("/api/gold-silver-ratio", {
        params: { range },
      });
      if (res.data.success) {
        return res.data.data;
      }
      throw new Error(res.data.message || "获取金银比失败");
    });
  } catch (err) {
    normalizeError(err);
  }
}

export async function fetchLast7Days(
  dataType: string
): Promise<Last7DaysData[]> {
  try {
    return await withRetry(async () => {
      const res = await api.get<ApiResponse<Last7DaysData[]>>("/api/last-7-days", {
        params: { data_type: dataType },
      });
      if (res.data.success) {
        return res.data.data;
      }
      throw new Error(res.data.message || "获取7日数据失败");
    });
  } catch (err) {
    normalizeError(err);
  }
}
