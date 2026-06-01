import { useEffect } from "react";
import AppLayout from "@/components/layout/AppLayout";
import PriceCard, { PriceCardSkeleton } from "@/components/PriceCard";
import PriceTrendChart from "@/components/PriceTrendChart";
import GoldSilverRatioChart from "@/components/GoldSilverRatioChart";
import usePriceStore from "@/stores/priceStore";

export default function Home() {
  const { goldPrice, silverPrice, loading, error, fetchOverview } =
    usePriceStore();

  useEffect(() => {
    fetchOverview();
    const interval = setInterval(fetchOverview, 60000);
    return () => clearInterval(interval);
  }, [fetchOverview]);

  const hasData = goldPrice || silverPrice;
  const isInitialLoading = loading && !hasData;

  return (
    <AppLayout
      hero={{
        eyebrow: "Koen · Precious Metals",
        title: "实时金价监控",
        subtitle:
          "黄金、白银回收价与大盘走势，自动刷新；数据来源于公开市场，仅供参考。",
      }}
    >
      {error && (
        <div className="mb-6 p-4 rounded-koen border border-red-500/40 bg-red-500/10 text-red-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button
            type="button"
            onClick={fetchOverview}
            className="ml-4 px-3 py-1 text-xs rounded-koen border border-red-500/30 hover:bg-red-500/20"
          >
            重试
          </button>
        </div>
      )}

      {isInitialLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <PriceCardSkeleton />
          <PriceCardSkeleton />
        </div>
      )}

      {!isInitialLoading && !hasData && !error && (
        <div className="mb-8 flex flex-col items-center justify-center py-16 text-[var(--v2-text-muted)]">
          <p className="text-lg font-medium text-[var(--v2-text-secondary)]">
            暂无价格数据
          </p>
          <p className="text-sm mt-1">请稍后刷新页面或检查网络连接</p>
        </div>
      )}

      {hasData && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <PriceCard
            name="黄金"
            price={goldPrice?.real_time_price ?? null}
            change={goldPrice?.change ?? null}
            changePct={goldPrice?.change_pct ?? null}
            high={goldPrice?.today_high ?? null}
            low={goldPrice?.today_low ?? null}
            updatedAt={goldPrice?.updated_at ?? null}
          />
          <PriceCard
            name="白银"
            price={silverPrice?.real_time_price ?? null}
            change={silverPrice?.change ?? null}
            changePct={silverPrice?.change_pct ?? null}
            high={silverPrice?.today_high ?? null}
            low={silverPrice?.today_low ?? null}
            updatedAt={silverPrice?.updated_at ?? null}
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <PriceTrendChart dataType="XAU" title="黄金走势" />
        <PriceTrendChart dataType="XAG" title="白银走势" />
      </div>

      <GoldSilverRatioChart />
    </AppLayout>
  );
}
