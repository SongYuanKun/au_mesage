import { useState, useEffect, useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { fetchGoldSilverRatio, type RatioData } from "@/api/price";
import { useTheme } from "@/hooks/useTheme";

type RangeOption = "30d" | "90d" | "1y";

const RANGE_LABELS: Record<RangeOption, string> = {
  "30d": "30天",
  "90d": "90天",
  "1y": "1年",
};

/** Custom tooltip props from Recharts */
interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string;
  strokeColor: string;
  tooltipBg: string;
  tooltipBorder: string;
  tooltipLabelColor: string;
}

/** Pre-defined heights for skeleton bars to avoid Math.random() on each render */
const SKELETON_HEIGHTS = [45, 72, 38, 85, 60, 33, 79, 52, 67, 41, 90, 55, 73, 48];

/** Loading skeleton for the ratio chart */
function ChartSkeleton() {
  return (
    <div className="h-full w-full flex flex-col justify-end gap-1 px-4 animate-pulse">
      <div className="flex items-end gap-1 h-full pt-4">
        {SKELETON_HEIGHTS.map((h, i) => (
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

/** Custom tooltip extracted as module-level component */
function CustomTooltipContent({
  active,
  payload,
  label,
  strokeColor,
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
      <p style={{ color: strokeColor }}>
        金银比：{Number(payload[0].value).toFixed(2)}
      </p>
    </div>
  );
}

export default function GoldSilverRatioChart() {
  const [range, setRange] = useState<RangeOption>("30d");
  const [data, setData] = useState<RatioData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const { isDark } = useTheme();

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchGoldSilverRatio(range)
      .then((result) => {
        if (!cancelled) {
          setData(result);
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
  }, [range, retryCount]);

  // Compute Y-axis domain: dataMin - 1% ~ dataMax + 1% (memoized)
  const yDomain = useMemo((): [number, number] | [string, string] => {
    if (data.length === 0) return ["auto", "auto"];
    const values = data.map((d) => d.ratio);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const padding = (max - min) * 0.01 || max * 0.01 || 1;
    return [
      parseFloat((min - padding).toFixed(2)),
      parseFloat((max + padding).toFixed(2)),
    ];
  }, [data]);

  // Dark mode adaptive colors
  const gridColor = isDark ? "rgba(75, 85, 99, 0.4)" : "#e5e7eb";
  const axisColor = isDark ? "#9ca3af" : "#6b7280";
  const strokeColor = isDark ? "#a78bfa" : "#8b5cf6";
  const tooltipBg = isDark ? "rgba(31, 41, 55, 0.95)" : "rgba(255, 255, 255, 0.95)";
  const tooltipBorder = isDark ? "#4b5563" : "#e5e7eb";
  const tooltipLabelColor = isDark ? "#e5e7eb" : "#374151";

  return (
    <div className="rounded-2xl shadow-lg border border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 p-6">
      {/* Header with tabs */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
            金银比走势
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            金价 / 银价 比率
          </p>
        </div>
        <div className="flex gap-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
          {(Object.keys(RANGE_LABELS) as RangeOption[]).map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={`px-3 py-1.5 text-sm rounded-md font-medium transition-colors ${
                range === r
                  ? "bg-white dark:bg-gray-600 text-purple-600 dark:text-purple-400 shadow-sm"
                  : "text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white"
              }`}
            >
              {RANGE_LABELS[r]}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="h-64">
        {loading ? (
          <ChartSkeleton />
        ) : error ? (
          <div className="h-full flex items-center justify-center text-red-400 text-sm">
            <div className="text-center">
              <p>⚠️ {error}</p>
              <button
                onClick={() => setRetryCount((c) => c + 1)}
                className="mt-2 text-xs text-blue-500 hover:text-blue-400 underline"
              >
                点击重试
              </button>
            </div>
          </div>
        ) : data.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-400 dark:text-gray-500">
            <svg className="w-12 h-12 mb-2 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <p className="text-sm">暂无金银比数据</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
              <XAxis
                dataKey="date"
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
                width={50}
                tickFormatter={(value: number) => value.toFixed(1)}
              />
              <Tooltip
                content={
                  <CustomTooltipContent
                    strokeColor={strokeColor}
                    tooltipBg={tooltipBg}
                    tooltipBorder={tooltipBorder}
                    tooltipLabelColor={tooltipLabelColor}
                  />
                }
              />
              <Line
                type="monotone"
                dataKey="ratio"
                stroke={strokeColor}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: strokeColor }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
