import { TrendingUp, TrendingDown } from "lucide-react";
import dayjs from "dayjs";

interface PriceCardProps {
  name: string;
  emoji?: string;
  price: number | null;
  change: number | null;
  changePct: number | null;
  high: number | null;
  low: number | null;
  updatedAt: string | null;
  loading?: boolean;
}

/** Pulse skeleton block */
function SkeletonBlock({ className }: { className?: string }) {
  return (
    <div
      className={`bg-gray-200 dark:bg-gray-700 rounded animate-pulse ${className || ""}`}
    />
  );
}

/** Skeleton variant of PriceCard for loading state */
export function PriceCardSkeleton() {
  return (
    <div className="koen-card p-6 animate-pulse">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <SkeletonBlock className="w-9 h-9 rounded-full" />
          <SkeletonBlock className="w-16 h-5" />
        </div>
        <SkeletonBlock className="w-16 h-6 rounded-full" />
      </div>
      <div className="mb-4">
        <SkeletonBlock className="w-32 h-9 mb-2" />
        <SkeletonBlock className="w-20 h-4" />
      </div>
      <div className="grid grid-cols-2 gap-3 mb-4">
        <SkeletonBlock className="h-16 rounded-lg" />
        <SkeletonBlock className="h-16 rounded-lg" />
      </div>
      <SkeletonBlock className="w-40 h-3" />
    </div>
  );
}

export default function PriceCard({
  name,
  emoji,
  price,
  change,
  changePct,
  high,
  low,
  updatedAt,
  loading,
}: PriceCardProps) {
  // Show skeleton if explicitly loading
  if (loading) {
    return <PriceCardSkeleton />;
  }

  const isUp = (change ?? 0) >= 0;

  return (
    <div className="koen-card p-6 transition-all hover:border-indigo-500/45">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          {emoji ? <span className="text-2xl">{emoji}</span> : null}
          <h2 className="text-lg font-semibold text-[var(--v2-text)]">{name}</h2>
        </div>
        {change !== null ? (
          <span
            className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-sm font-medium ${
              isUp
                ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
            }`}
          >
            {isUp ? (
              <TrendingUp className="w-3.5 h-3.5" />
            ) : (
              <TrendingDown className="w-3.5 h-3.5" />
            )}
            {isUp ? "+" : ""}
            {changePct !== null ? changePct.toFixed(2) : "--"}%
          </span>
        ) : (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400">
            --
          </span>
        )}
      </div>

      {/* Price */}
      <div className="mb-4">
        <p className="text-3xl font-bold text-[var(--v2-text)]">
          {price !== null ? `¥${price.toFixed(2)}` : "--"}
        </p>
        {change !== null ? (
          <p
            className={`text-sm mt-1 ${
              isUp ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
            }`}
          >
            {isUp ? "+" : ""}
            {change.toFixed(2)} 元
          </p>
        ) : (
          <p className="text-sm mt-1 text-gray-400 dark:text-gray-500">--</p>
        )}
      </div>

      {/* High / Low */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="rounded-koen border border-[var(--v2-border)] bg-[var(--v2-surface-hover)] p-3">
          <p className="text-xs text-[var(--v2-text-muted)]">今日最高</p>
          <p className="text-sm font-semibold text-[var(--v2-text)]">
            {high !== null ? `¥${high.toFixed(2)}` : "--"}
          </p>
        </div>
        <div className="rounded-koen border border-[var(--v2-border)] bg-[var(--v2-surface-hover)] p-3">
          <p className="text-xs text-[var(--v2-text-muted)]">今日最低</p>
          <p className="text-sm font-semibold text-[var(--v2-text)]">
            {low !== null ? `¥${low.toFixed(2)}` : "--"}
          </p>
        </div>
      </div>

      {/* Updated At */}
      <p className="text-xs text-[var(--v2-text-muted)]">
        更新时间：{updatedAt ? dayjs(updatedAt).format("MM-DD HH:mm:ss") : "--"}
      </p>
    </div>
  );
}
