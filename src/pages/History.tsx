import { useState, useEffect, useMemo, useCallback } from "react";
import {
  AreaChart,
  Area,
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { Download, Calendar, RefreshCw } from "lucide-react";
import Navbar from "@/components/Navbar";
import {
  fetchPriceTrend,
  fetchExportHistory,
  type CandlestickData,
  type LineData,
} from "@/api/price";
import { useTheme } from "@/hooks/useTheme";

/** 品类选项 */
type DataTypeOption = "黄金" | "白银";

/** 区间选项 */
type RangeOption = "1d" | "7d" | "30d" | "90d" | "1y" | "all";

const RANGE_LABELS: Record<RangeOption, string> = {
  "1d": "今日",
  "7d": "7天",
  "30d": "30天",
  "90d": "90天",
  "1y": "1年",
  all: "全部",
};

const DATA_TYPE_LABELS: Record<DataTypeOption, string> = {
  "黄金": "🥇 黄金",
  "白银": "🥈 白银",
};

/** 导出格式 */
type ExportFormat = "csv" | "json";

/** 分时线数据点 */
interface ChartLinePoint {
  name: string;
  value: number;
}

/** K线数据点（用于 ComposedChart） */
interface ChartCandlePoint {
  name: string;
  open: number;
  high: number;
  low: number;
  close: number;
  isUp: boolean;
}

/** Custom tooltip props */
interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ value: number; dataKey?: string }>;
  label?: string;
  tooltipBg: string;
  tooltipBorder: string;
  tooltipLabelColor: string;
  isCandle?: boolean;
}

/** Loading skeleton */
function ChartSkeleton() {
  const heights = [52, 78, 43, 91, 65, 38, 84, 57, 70, 46, 88, 61, 55, 72];
  return (
    <div className="h-full w-full flex flex-col justify-end gap-1 px-4 animate-pulse">
      <div className="flex items-end gap-1 h-full pt-4">
        {heights.map((h, i) => (
          <div
            key={i}
            className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-t"
            style={{ height: `${h}%` }}
          />
        ))}
      </div>
      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full" />
    </div>
  );
}

/** 分时线 Tooltip */
function LineTooltipContent({
  active,
  payload,
  label,
  tooltipBg,
  tooltipBorder,
  tooltipLabelColor,
}: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div
      className="rounded-lg px-3 py-2 shadow-lg text-sm"
      style={{
        backgroundColor: tooltipBg,
        border: `1px solid ${tooltipBorder}`,
      }}
    >
      <p className="font-medium" style={{ color: tooltipLabelColor }}>
        {label}
      </p>
      <p style={{ color: "#3b82f6" }}>
        价格：¥{Number(payload[0].value).toFixed(2)}
      </p>
    </div>
  );
}

/** K线 Tooltip */
function CandleTooltipContent({
  active,
  payload,
  label,
  tooltipBg,
  tooltipBorder,
  tooltipLabelColor,
}: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  // 找到 close 值判断涨跌
  const closeVal = payload.find((p) => p.dataKey === "close");
  const openVal = payload.find((p) => p.dataKey === "open");
  const highVal = payload.find((p) => p.dataKey === "high");
  const lowVal = payload.find((p) => p.dataKey === "low");
  const color = closeVal && openVal && closeVal.value >= openVal.value ? "#22c55e" : "#ef4444";
  return (
    <div
      className="rounded-lg px-3 py-2 shadow-lg text-sm"
      style={{
        backgroundColor: tooltipBg,
        border: `1px solid ${tooltipBorder}`,
      }}
    >
      <p className="font-medium" style={{ color: tooltipLabelColor }}>
        {label}
      </p>
      <p style={{ color }}>开：{openVal ? `¥${Number(openVal.value).toFixed(2)}` : "--"}</p>
      <p style={{ color }}>高：{highVal ? `¥${Number(highVal.value).toFixed(2)}` : "--"}</p>
      <p style={{ color }}>低：{lowVal ? `¥${Number(lowVal.value).toFixed(2)}` : "--"}</p>
      <p style={{ color }}>收：{closeVal ? `¥${Number(closeVal.value).toFixed(2)}` : "--"}</p>
    </div>
  );
}

export default function History() {
  const [dataType, setDataType] = useState<DataTypeOption>("黄金");
  const [range, setRange] = useState<RangeOption>("7d");
  const [chartType, setChartType] = useState<string>("line");
  const [rawData, setRawData] = useState<(CandlestickData | LineData)[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  // 导出表单状态
  const [exportStartDate, setExportStartDate] = useState("");
  const [exportEndDate, setExportEndDate] = useState("");
  const [exportFormat, setExportFormat] = useState<ExportFormat>("csv");
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const { isDark } = useTheme();

  // 获取趋势数据
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchPriceTrend(dataType, range)
      .then((result) => {
        if (!cancelled) {
          setChartType(result.chart_type);
          setRawData(result.data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message);
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [dataType, range, retryCount]);

  // 将原始数据归一化为分时线数据
  const lineChartData: ChartLinePoint[] = useMemo(
    () =>
      rawData.map((item) => {
        if ("price" in item) {
          return { name: item.time, value: item.price };
        }
        return { name: item.date, value: item.close };
      }),
    [rawData]
  );

  // 将原始数据归一化为K线数据
  const candleChartData: ChartCandlePoint[] = useMemo(
    () =>
      rawData
        .filter((item): item is CandlestickData => "open" in item)
        .map((item) => ({
          name: item.date,
          open: item.open,
          high: item.high,
          low: item.low,
          close: item.close,
          isUp: item.close >= item.open,
        })),
    [rawData]
  );

  // 计算 Y 轴范围
  const yDomain = useMemo((): [number, number] | [string, string] => {
    if (chartType === "candlestick") {
      if (candleChartData.length === 0) return ["auto", "auto"];
      const values = candleChartData.flatMap((d) => [d.high, d.low]);
      const min = Math.min(...values);
      const max = Math.max(...values);
      const padding = (max - min) * 0.01 || max * 0.01 || 1;
      return [
        parseFloat((min - padding).toFixed(2)),
        parseFloat((max + padding).toFixed(2)),
      ];
    }
    if (lineChartData.length === 0) return ["auto", "auto"];
    const values = lineChartData.map((d) => d.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const padding = (max - min) * 0.01 || max * 0.01 || 1;
    return [
      parseFloat((min - padding).toFixed(2)),
      parseFloat((max + padding).toFixed(2)),
    ];
  }, [chartType, lineChartData, candleChartData]);

  // 暗色模式颜色
  const gridColor = isDark ? "rgba(75, 85, 99, 0.4)" : "#e5e7eb";
  const axisColor = isDark ? "#9ca3af" : "#6b7280";
  const strokeColor = isDark ? "#60a5fa" : "#3b82f6";
  const gradientStart = isDark ? "rgba(96, 165, 250, 0.3)" : "rgba(59, 130, 246, 0.3)";
  const gradientEnd = isDark ? "rgba(96, 165, 250, 0)" : "rgba(59, 130, 246, 0)";
  const tooltipBg = isDark ? "rgba(31, 41, 55, 0.95)" : "rgba(255, 255, 255, 0.95)";
  const tooltipBorder = isDark ? "#4b5563" : "#e5e7eb";
  const tooltipLabelColor = isDark ? "#e5e7eb" : "#374151";

  // 导出历史数据
  const handleExport = useCallback(async () => {
    if (!exportStartDate || !exportEndDate) {
      setExportError("请选择日期范围");
      return;
    }
    setExporting(true);
    setExportError(null);
    try {
      await fetchExportHistory(dataType, exportStartDate, exportEndDate, exportFormat);
    } catch (err) {
      setExportError(err instanceof Error ? err.message : "导出失败");
    } finally {
      setExporting(false);
    }
  }, [dataType, exportStartDate, exportEndDate, exportFormat]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 页面标题 */}
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          📈 历史趋势
        </h2>

        {/* 品类切换 + 区间选择器 */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
          {/* 品类切换 */}
          <div className="flex gap-2">
            {(Object.keys(DATA_TYPE_LABELS) as DataTypeOption[]).map((dt) => (
              <button
                key={dt}
                onClick={() => setDataType(dt)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
                  dataType === dt
                    ? "bg-blue-600 text-white shadow-md"
                    : "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                }`}
              >
                {DATA_TYPE_LABELS[dt]}
              </button>
            ))}
          </div>

          {/* 区间选择器 */}
          <div className="flex gap-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
            {(Object.keys(RANGE_LABELS) as RangeOption[]).map((r) => (
              <button
                key={r}
                onClick={() => setRange(r)}
                className={`px-3 py-1.5 text-sm rounded-md font-medium transition-colors ${
                  range === r
                    ? "bg-white dark:bg-gray-600 text-blue-600 dark:text-blue-400 shadow-sm"
                    : "text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white"
                }`}
              >
                {RANGE_LABELS[r]}
              </button>
            ))}
          </div>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm flex items-center justify-between">
            <span>⚠️ {error}</span>
            <button
              onClick={() => setRetryCount((c) => c + 1)}
              className="ml-4 px-3 py-1 text-xs rounded-lg bg-red-100 dark:bg-red-900/40 hover:bg-red-200 dark:hover:bg-red-900/60 transition-colors flex items-center gap-1"
            >
              <RefreshCw className="w-3 h-3" />
              重试
            </button>
          </div>
        )}

        {/* 大图表 */}
        <div className="rounded-2xl shadow-lg border border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 p-6 mb-8">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4">
            {dataType}价格走势（{RANGE_LABELS[range]}）
          </h3>
          <div className="h-80">
            {loading ? (
              <ChartSkeleton />
            ) : error ? null : chartType === "line" ? (
              lineChartData.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-gray-400 dark:text-gray-500">
                  <svg className="w-12 h-12 mb-2 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  <p className="text-sm">暂无{dataType}趋势数据</p>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={lineChartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                    <defs>
                      <linearGradient id={`history-gradient-${dataType}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={gradientStart} stopOpacity={1} />
                        <stop offset="95%" stopColor={gradientEnd} stopOpacity={1} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                    <XAxis
                      dataKey="name"
                      tick={{ fontSize: 12, fill: axisColor }}
                      stroke={axisColor}
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis
                      domain={yDomain}
                      tick={{ fontSize: 12, fill: axisColor }}
                      stroke={axisColor}
                      tickLine={false}
                      axisLine={false}
                      width={60}
                      tickFormatter={(value: number) => value.toFixed(0)}
                    />
                    <Tooltip
                      content={
                        <LineTooltipContent
                          tooltipBg={tooltipBg}
                          tooltipBorder={tooltipBorder}
                          tooltipLabelColor={tooltipLabelColor}
                        />
                      }
                    />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke={strokeColor}
                      strokeWidth={2}
                      fill={`url(#history-gradient-${dataType})`}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )
            ) : candleChartData.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-gray-400 dark:text-gray-500">
                <svg className="w-12 h-12 mb-2 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <p className="text-sm">暂无{dataType}K线数据</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={candleChartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                  <XAxis
                    dataKey="name"
                    tick={{ fontSize: 11, fill: axisColor }}
                    stroke={axisColor}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    domain={yDomain}
                    tick={{ fontSize: 12, fill: axisColor }}
                    stroke={axisColor}
                    tickLine={false}
                    axisLine={false}
                    width={60}
                    tickFormatter={(value: number) => value.toFixed(0)}
                  />
                  <Tooltip
                    content={
                      <CandleTooltipContent
                        tooltipBg={tooltipBg}
                        tooltipBorder={tooltipBorder}
                        tooltipLabelColor={tooltipLabelColor}
                        isCandle
                      />
                    }
                  />
                  {/* 影线区域：用 Bar 显示 high-low */}
                  <Bar dataKey="high" fill="transparent" isAnimationActive={false} />
                  <Bar dataKey="low" fill="transparent" isAnimationActive={false} />
                  {/* 主体：open-close 柱体 */}
                  <Bar dataKey="close" isAnimationActive={false} radius={[2, 2, 0, 0]}>
                    {candleChartData.map((entry, index) => (
                      <Cell
                        key={`candle-${index}`}
                        fill={entry.isUp ? "#22c55e" : "#ef4444"}
                        opacity={0.9}
                      />
                    ))}
                  </Bar>
                </ComposedChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* 图表类型提示 */}
          {!loading && !error && (lineChartData.length > 0 || candleChartData.length > 0) && (
            <p className="mt-3 text-xs text-gray-400 dark:text-gray-500 text-right">
              图表类型：{chartType === "candlestick" ? "K线(OHLC)" : "分时线"}
            </p>
          )}
        </div>

        {/* 导出表单 */}
        <div className="rounded-2xl shadow-lg border border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 p-6">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4 flex items-center gap-2">
            <Download className="w-5 h-5" />
            导出历史数据
          </h3>

          {exportError && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm">
              ⚠️ {exportError}
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* 开始日期 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                <Calendar className="w-4 h-4 inline mr-1" />
                开始日期
              </label>
              <input
                type="date"
                value={exportStartDate}
                onChange={(e) => setExportStartDate(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-colors"
              />
            </div>

            {/* 结束日期 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                <Calendar className="w-4 h-4 inline mr-1" />
                结束日期
              </label>
              <input
                type="date"
                value={exportEndDate}
                onChange={(e) => setExportEndDate(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-colors"
              />
            </div>

            {/* 格式选择 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                导出格式
              </label>
              <select
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value as ExportFormat)}
                className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-colors"
              >
                <option value="csv">CSV</option>
                <option value="json">JSON</option>
              </select>
            </div>

            {/* 导出按钮 */}
            <div className="flex items-end">
              <button
                onClick={handleExport}
                disabled={exporting}
                className="w-full px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {exporting ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    导出中...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    导出
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="text-center text-xs text-gray-400 dark:text-gray-500 mt-8 pb-8">
          数据来源于公开市场 · 仅供参考
        </footer>
      </main>
    </div>
  );
}
