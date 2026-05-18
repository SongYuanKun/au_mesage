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
import { Calculator, TrendingUp, TrendingDown, RefreshCw } from "lucide-react";
import Navbar from "@/components/Navbar";
import {
  fetchGoldSilverRatio,
  calculatePriceDiff,
  compareHistory,
  type RatioData,
  type CalculateResult,
  type HistoryCompareResult,
} from "@/api/price";
import { useTheme } from "@/hooks/useTheme";

/** 金银比区间选项 */
type RatioRangeOption = "30d" | "90d" | "1y";

const RATIO_RANGE_LABELS: Record<RatioRangeOption, string> = {
  "30d": "30天",
  "90d": "90天",
  "1y": "1年",
};

/** 品类选项 */
type DataTypeOption = "黄金" | "白银";

/** Tooltip props */
interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string;
  strokeColor: string;
  tooltipBg: string;
  tooltipBorder: string;
  tooltipLabelColor: string;
}

/** Loading skeleton */
function ChartSkeleton() {
  const heights = [45, 72, 38, 85, 60, 33, 79, 52, 67, 41, 90, 55, 73, 48];
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

/** 金银比 Tooltip */
function RatioTooltipContent({
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

export default function Analysis() {
  const { isDark } = useTheme();

  // ===== 金银比图表状态 =====
  const [ratioRange, setRatioRange] = useState<RatioRangeOption>("30d");
  const [ratioData, setRatioData] = useState<RatioData[]>([]);
  const [ratioLoading, setRatioLoading] = useState(false);
  const [ratioError, setRatioError] = useState<string | null>(null);
  const [ratioRetryCount, setRatioRetryCount] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setRatioLoading(true);
    setRatioError(null);

    fetchGoldSilverRatio(ratioRange)
      .then((result) => {
        if (!cancelled) {
          setRatioData(result);
          setRatioLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setRatioError(err.message);
          setRatioLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [ratioRange, ratioRetryCount]);

  // 金银比 Y 轴范围
  const ratioYDomain = useMemo((): [number, number] | [string, string] => {
    if (ratioData.length === 0) return ["auto", "auto"];
    const values = ratioData.map((d) => d.ratio);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const padding = (max - min) * 0.01 || max * 0.01 || 1;
    return [
      parseFloat((min - padding).toFixed(2)),
      parseFloat((max + padding).toFixed(2)),
    ];
  }, [ratioData]);

  // ===== 价差计算器状态 =====
  const [calcDataType, setCalcDataType] = useState<DataTypeOption>("黄金");
  const [calcProductPrice, setCalcProductPrice] = useState<string>("");
  const [calcWeight, setCalcWeight] = useState<string>("");
  const [calcLoading, setCalcLoading] = useState(false);
  const [calcResult, setCalcResult] = useState<CalculateResult | null>(null);
  const [calcError, setCalcError] = useState<string | null>(null);

  const handleCalculate = async () => {
    const price = parseFloat(calcProductPrice);
    const weight = parseFloat(calcWeight);
    if (isNaN(price) || isNaN(weight) || price <= 0 || weight <= 0) {
      setCalcError("请输入有效的价格和克重");
      return;
    }
    setCalcLoading(true);
    setCalcError(null);
    setCalcResult(null);
    try {
      const result = await calculatePriceDiff(price, weight, calcDataType);
      setCalcResult(result);
    } catch (err) {
      setCalcError(err instanceof Error ? err.message : "计算失败");
    } finally {
      setCalcLoading(false);
    }
  };

  // ===== 历史对比状态 =====
  const [histDataType, setHistDataType] = useState<DataTypeOption>("黄金");
  const [histProductPrice, setHistProductPrice] = useState<string>("");
  const [histWeight, setHistWeight] = useState<string>("");
  const [histLoading, setHistLoading] = useState(false);
  const [histResult, setHistResult] = useState<HistoryCompareResult | null>(null);
  const [histError, setHistError] = useState<string | null>(null);

  const handleCompare = async () => {
    const price = parseFloat(histProductPrice);
    const weight = parseFloat(histWeight);
    if (isNaN(price) || isNaN(weight) || price <= 0 || weight <= 0) {
      setHistError("请输入有效的价格和克重");
      return;
    }
    setHistLoading(true);
    setHistError(null);
    setHistResult(null);
    try {
      const result = await compareHistory(price, weight, histDataType);
      setHistResult(result);
    } catch (err) {
      setHistError(err instanceof Error ? err.message : "对比失败");
    } finally {
      setHistLoading(false);
    }
  };

  // ===== 暗色模式颜色 =====
  const gridColor = isDark ? "rgba(75, 85, 99, 0.4)" : "#e5e7eb";
  const axisColor = isDark ? "#9ca3af" : "#6b7280";
  const ratioStrokeColor = isDark ? "#a78bfa" : "#8b5cf6";
  const tooltipBg = isDark ? "rgba(31, 41, 55, 0.95)" : "rgba(255, 255, 255, 0.95)";
  const tooltipBorder = isDark ? "#4b5563" : "#e5e7eb";
  const tooltipLabelColor = isDark ? "#e5e7eb" : "#374151";

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 页面标题 */}
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
          📊 分析工具
        </h2>

        {/* 金银比图表 */}
        <div className="rounded-2xl shadow-lg border border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 p-6 mb-8">
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
              {(Object.keys(RATIO_RANGE_LABELS) as RatioRangeOption[]).map((r) => (
                <button
                  key={r}
                  onClick={() => setRatioRange(r)}
                  className={`px-3 py-1.5 text-sm rounded-md font-medium transition-colors ${
                    ratioRange === r
                      ? "bg-white dark:bg-gray-600 text-purple-600 dark:text-purple-400 shadow-sm"
                      : "text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white"
                  }`}
                >
                  {RATIO_RANGE_LABELS[r]}
                </button>
              ))}
            </div>
          </div>

          <div className="h-64">
            {ratioLoading ? (
              <ChartSkeleton />
            ) : ratioError ? (
              <div className="h-full flex items-center justify-center text-red-400 text-sm">
                <div className="text-center">
                  <p>⚠️ {ratioError}</p>
                  <button
                    onClick={() => setRatioRetryCount((c) => c + 1)}
                    className="mt-2 text-xs text-blue-500 hover:text-blue-400 underline"
                  >
                    点击重试
                  </button>
                </div>
              </div>
            ) : ratioData.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-gray-400 dark:text-gray-500">
                <svg className="w-12 h-12 mb-2 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <p className="text-sm">暂无金银比数据</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={ratioData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12, fill: axisColor }}
                    stroke={axisColor}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    domain={ratioYDomain}
                    tick={{ fontSize: 12, fill: axisColor }}
                    stroke={axisColor}
                    tickLine={false}
                    axisLine={false}
                    width={50}
                    tickFormatter={(value: number) => value.toFixed(1)}
                  />
                  <Tooltip
                    content={
                      <RatioTooltipContent
                        strokeColor={ratioStrokeColor}
                        tooltipBg={tooltipBg}
                        tooltipBorder={tooltipBorder}
                        tooltipLabelColor={tooltipLabelColor}
                      />
                    }
                  />
                  <Line
                    type="monotone"
                    dataKey="ratio"
                    stroke={ratioStrokeColor}
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, fill: ratioStrokeColor }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* 工具区域：价差计算器 + 历史对比 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* 价差计算器 */}
          <div className="rounded-2xl shadow-lg border border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 p-6">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4 flex items-center gap-2">
              <Calculator className="w-5 h-5" />
              价差计算器
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              输入产品总价和克重，计算与实时价格的价差
            </p>

            {/* 品类选择 */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                品类
              </label>
              <div className="flex gap-2">
                {(["黄金", "白银"] as DataTypeOption[]).map((dt) => (
                  <button
                    key={dt}
                    onClick={() => setCalcDataType(dt)}
                    className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      calcDataType === dt
                        ? "bg-blue-600 text-white"
                        : "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                    }`}
                  >
                    {dt === "黄金" ? "🥇" : "🥈"} {dt}
                  </button>
                ))}
              </div>
            </div>

            {/* 产品总价 */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                产品总价（元）
              </label>
              <input
                type="number"
                value={calcProductPrice}
                onChange={(e) => setCalcProductPrice(e.target.value)}
                placeholder="例如：58000"
                className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-colors"
              />
            </div>

            {/* 克重 */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                克重（克）
              </label>
              <input
                type="number"
                value={calcWeight}
                onChange={(e) => setCalcWeight(e.target.value)}
                placeholder="例如：10"
                className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-colors"
              />
            </div>

            {/* 计算按钮 */}
            <button
              onClick={handleCalculate}
              disabled={calcLoading}
              className="w-full px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {calcLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  计算中...
                </>
              ) : (
                <>
                  <Calculator className="w-4 h-4" />
                  开始计算
                </>
              )}
            </button>

            {/* 计算结果 */}
            {calcError && (
              <div className="mt-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm">
                ⚠️ {calcError}
              </div>
            )}

            {calcResult && (
              <div className="mt-4 space-y-3">
                <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                  <p className="text-xs text-gray-500 dark:text-gray-400">实时单价</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    ¥{calcResult.real_time_price.toFixed(2)}/克
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                  <p className="text-xs text-gray-500 dark:text-gray-400">产品单价</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    ¥{calcResult.product_price_per_gram.toFixed(2)}/克
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                  <p className="text-xs text-gray-500 dark:text-gray-400">价差（每克）</p>
                  <p className={`text-lg font-semibold flex items-center gap-1 ${
                    calcResult.diff >= 0
                      ? "text-green-600 dark:text-green-400"
                      : "text-red-600 dark:text-red-400"
                  }`}>
                    {calcResult.diff >= 0 ? (
                      <TrendingUp className="w-4 h-4" />
                    ) : (
                      <TrendingDown className="w-4 h-4" />
                    )}
                    ¥{calcResult.diff.toFixed(2)}/克
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                  <p className="text-xs text-gray-500 dark:text-gray-400">总盈亏</p>
                  <p className={`text-lg font-semibold ${
                    calcResult.total_diff >= 0
                      ? "text-green-600 dark:text-green-400"
                      : "text-red-600 dark:text-red-400"
                  }`}>
                    {calcResult.total_diff >= 0 ? "+" : ""}
                    ¥{calcResult.total_diff.toFixed(2)}
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* 历史对比 */}
          <div className="rounded-2xl shadow-lg border border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 p-6">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              历史对比
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              输入购买信息，查看当前价格下的盈亏情况
            </p>

            {/* 品类选择 */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                品类
              </label>
              <div className="flex gap-2">
                {(["黄金", "白银"] as DataTypeOption[]).map((dt) => (
                  <button
                    key={dt}
                    onClick={() => setHistDataType(dt)}
                    className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      histDataType === dt
                        ? "bg-blue-600 text-white"
                        : "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                    }`}
                  >
                    {dt === "黄金" ? "🥇" : "🥈"} {dt}
                  </button>
                ))}
              </div>
            </div>

            {/* 购买总价 */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                购买总价（元）
              </label>
              <input
                type="number"
                value={histProductPrice}
                onChange={(e) => setHistProductPrice(e.target.value)}
                placeholder="例如：58000"
                className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-colors"
              />
            </div>

            {/* 克重 */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                克重（克）
              </label>
              <input
                type="number"
                value={histWeight}
                onChange={(e) => setHistWeight(e.target.value)}
                placeholder="例如：10"
                className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-colors"
              />
            </div>

            {/* 对比按钮 */}
            <button
              onClick={handleCompare}
              disabled={histLoading}
              className="w-full px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {histLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  对比中...
                </>
              ) : (
                <>
                  <TrendingUp className="w-4 h-4" />
                  开始对比
                </>
              )}
            </button>

            {/* 对比结果 */}
            {histError && (
              <div className="mt-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm">
                ⚠️ {histError}
              </div>
            )}

            {histResult && (
              <div className="mt-4 space-y-3">
                <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                  <p className="text-xs text-gray-500 dark:text-gray-400">购买单价</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    ¥{histResult.purchase_price_per_gram.toFixed(2)}/克
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                  <p className="text-xs text-gray-500 dark:text-gray-400">当前实时单价</p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white">
                    ¥{histResult.current_price.toFixed(2)}/克
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                  <p className="text-xs text-gray-500 dark:text-gray-400">盈亏（每克）</p>
                  <p className={`text-lg font-semibold flex items-center gap-1 ${
                    histResult.profit_per_gram >= 0
                      ? "text-green-600 dark:text-green-400"
                      : "text-red-600 dark:text-red-400"
                  }`}>
                    {histResult.profit_per_gram >= 0 ? (
                      <TrendingUp className="w-4 h-4" />
                    ) : (
                      <TrendingDown className="w-4 h-4" />
                    )}
                    {histResult.profit_per_gram >= 0 ? "+" : ""}
                    ¥{histResult.profit_per_gram.toFixed(2)}/克
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                  <p className="text-xs text-gray-500 dark:text-gray-400">总盈亏</p>
                  <p className={`text-lg font-semibold ${
                    histResult.total_profit >= 0
                      ? "text-green-600 dark:text-green-400"
                      : "text-red-600 dark:text-red-400"
                  }`}>
                    {histResult.total_profit >= 0 ? "+" : ""}
                    ¥{histResult.total_profit.toFixed(2)}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <footer className="text-center text-xs text-gray-400 dark:text-gray-500 pb-8">
          数据来源于公开市场 · 仅供参考
        </footer>
      </main>
    </div>
  );
}
