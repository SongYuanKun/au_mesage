import { create } from "zustand";
import { fetchPriceOverview, type PriceOverviewItem } from "@/api/price";

interface PriceState {
  goldPrice: PriceOverviewItem | null;
  silverPrice: PriceOverviewItem | null;
  loading: boolean;
  error: string | null;
  lastFetchedAt: number | null;
  fetchOverview: () => Promise<void>;
}

const usePriceStore = create<PriceState>((set, get) => ({
  goldPrice: null,
  silverPrice: null,
  loading: false,
  error: null,
  lastFetchedAt: null,

  fetchOverview: async () => {
    // Prevent concurrent fetches
    if (get().loading) return;

    set({ loading: true, error: null });
    try {
      const data = await fetchPriceOverview();
      const gold = data.find((item) => item.data_type === "黄金") || null;
      const silver = data.find((item) => item.data_type === "白银") || null;
      set({
        goldPrice: gold,
        silverPrice: silver,
        loading: false,
        lastFetchedAt: Date.now(),
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "未知错误";
      set({ error: message, loading: false });
    }
  },
}));

export default usePriceStore;
