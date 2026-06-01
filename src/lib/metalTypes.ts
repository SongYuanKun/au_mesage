/** 展示用金属键（与 Flask metal-series 国际优先一致） */
export type MetalKey = "gold" | "silver";

export const METAL_LABEL: Record<MetalKey, string> = {
  gold: "黄金",
  silver: "白银",
};

/** 趋势 / K 线 API 的 data_type（国际代码） */
export function apiTrendDataType(metal: MetalKey): string {
  return metal === "gold" ? "XAU" : "XAG";
}

/** 国内品类名（overview、部分历史接口） */
export function apiDomesticDataType(metal: MetalKey): string {
  return metal === "gold" ? "黄 金" : "白 银";
}
