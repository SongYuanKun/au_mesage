import { useEffect } from "react";
import Navbar from "@/components/Navbar";
import PriceCard, { PriceCardSkeleton } from "@/components/PriceCard";
import PriceTrendChart from "@/components/PriceTrendChart";
import GoldSilverRatioChart from "@/components/GoldSilverRatioChart";
import SharePriceCard from "@/components/SharePriceCard";
import usePriceStore from "@/stores/priceStore";

export default function Home() {
  const { goldPrice, silverPrice, loading, error, fetchOverview } =
    usePriceStore();

  useEffect(() => {
    fetchOverview();
    // Auto-refresh every 60 seconds
    const interval = setInterval(fetchOverview, 60000);
    return () => clearInterval(interval);
  }, [fetchOverview]);

  const hasData = goldPrice || silverPrice;
  const isInitialLoading = loading && !hasData;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Banner */}
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm flex items-center justify-between">
            <span>⚠️ {error}</span>
            <button
              onClick={fetchOverview}
              className="ml-4 px-3 py-1 text-xs rounded-lg bg-red-100 dark:bg-red-900/40 hover:bg-red-200 dark:hover:bg-red-900/60 transition-colors"
            >
              重试
            </button>
          </div>
        )}

        {/* Loading Skeleton */}
        {isInitialLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <PriceCardSkeleton />
            <PriceCardSkeleton />
          </div>
        )}

        {/* Empty State - no error, no loading, no data */}
        {!isInitialLoading && !hasData && !error && (
          <div className="mb-8 flex flex-col items-center justify-center py-16 text-gray-400 dark:text-gray-500">
            <svg className="w-16 h-16 mb-4 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
            <p className="text-lg font-medium">暂无价格数据</p>
            <p className="text-sm mt-1">请稍后刷新页面或检查网络连接</p>
          </div>
        )}

        {/* Price Cards */}
        {hasData && (
          <>
            <SharePriceCard goldPrice={goldPrice} silverPrice={silverPrice} />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <PriceCard
                name="黄金"
                emoji="🥇"
                price={goldPrice?.real_time_price ?? null}
                change={goldPrice?.change ?? null}
                changePct={goldPrice?.change_pct ?? null}
                high={goldPrice?.today_high ?? null}
                low={goldPrice?.today_low ?? null}
                updatedAt={goldPrice?.updated_at ?? null}
              />
              <PriceCard
                name="白银"
                emoji="🥈"
                price={silverPrice?.real_time_price ?? null}
                change={silverPrice?.change ?? null}
                changePct={silverPrice?.change_pct ?? null}
                high={silverPrice?.today_high ?? null}
                low={silverPrice?.today_low ?? null}
                updatedAt={silverPrice?.updated_at ?? null}
              />
            </div>
          </>
        )}

        {/* Price Trend Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <PriceTrendChart dataType="黄金" />
          <PriceTrendChart dataType="白银" />
        </div>

        {/* Gold Silver Ratio Chart */}
        <div className="mb-8">
          <GoldSilverRatioChart />
        </div>

        {/* Footer */}
        <footer className="text-center text-xs text-gray-400 dark:text-gray-500 pb-8">
          数据来源于公开市场 · 仅供参考 · 每分钟自动刷新
        </footer>
      </main>
    </div>
  );
}
