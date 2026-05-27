import { useMemo, useState } from "react";
import { Download, Share2, X } from "lucide-react";
import dayjs from "dayjs";
import type { PriceOverviewItem } from "@/api/price";

interface SharePriceCardProps {
  goldPrice: PriceOverviewItem | null;
  silverPrice: PriceOverviewItem | null;
}

const CARD_WIDTH = 1080;
const CARD_HEIGHT = 1440;
const SITE_URL = "au.songyuankun.top";

function formatPrice(value: number | null | undefined) {
  return typeof value === "number" ? "¥" + value.toFixed(2) : "--";
}

function formatChange(value: number | null | undefined) {
  if (typeof value !== "number") return "--";
  return (value >= 0 ? "+" : "") + value.toFixed(2) + "%";
}

function latestUpdatedAt(items: Array<PriceOverviewItem | null>) {
  const times = items
    .map((item) => (item?.updated_at ? dayjs(item.updated_at) : null))
    .filter((item): item is dayjs.Dayjs => Boolean(item));
  if (!times.length) return dayjs();
  return times.reduce((latest, current) => (current.isAfter(latest) ? current : latest), times[0]);
}

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  width: number,
  height: number,
  radius: number
) {
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.arcTo(x + width, y, x + width, y + height, radius);
  ctx.arcTo(x + width, y + height, x, y + height, radius);
  ctx.arcTo(x, y + height, x, y, radius);
  ctx.arcTo(x, y, x + radius, y, radius);
  ctx.closePath();
}

function drawPriceRow(
  ctx: CanvasRenderingContext2D,
  label: string,
  item: PriceOverviewItem | null,
  y: number,
  accent: string
) {
  roundRect(ctx, 84, y, 912, 280, 36);
  ctx.fillStyle = "rgba(255, 255, 255, 0.92)";
  ctx.fill();

  ctx.fillStyle = accent;
  ctx.font = "700 36px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
  ctx.fillText(label, 132, y + 78);

  ctx.fillStyle = "#111827";
  ctx.font = "800 82px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
  ctx.fillText(formatPrice(item?.real_time_price), 132, y + 174);

  const changePct = item?.change_pct ?? null;
  const isUp = (changePct ?? 0) >= 0;
  ctx.fillStyle = isUp ? "#059669" : "#dc2626";
  ctx.font = "700 34px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
  ctx.fillText((isUp ? "上涨 " : "下跌 ") + formatChange(changePct), 704, y + 92);

  ctx.fillStyle = "#6b7280";
  ctx.font = "500 28px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
  ctx.fillText("最高 " + formatPrice(item?.today_high), 704, y + 158);
  ctx.fillText("最低 " + formatPrice(item?.today_low), 704, y + 208);
}

function generateShareImage(goldPrice: PriceOverviewItem | null, silverPrice: PriceOverviewItem | null) {
  const canvas = document.createElement("canvas");
  canvas.width = CARD_WIDTH;
  canvas.height = CARD_HEIGHT;
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    throw new Error("当前浏览器不支持图片生成");
  }

  const bg = ctx.createLinearGradient(0, 0, CARD_WIDTH, CARD_HEIGHT);
  bg.addColorStop(0, "#fff7ed");
  bg.addColorStop(0.5, "#f8fafc");
  bg.addColorStop(1, "#eef2ff");
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, CARD_WIDTH, CARD_HEIGHT);

  ctx.fillStyle = "rgba(245, 158, 11, 0.18)";
  ctx.beginPath();
  ctx.arc(940, 160, 220, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#111827";
  ctx.font = "800 68px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
  ctx.fillText("今日金银价", 84, 160);

  ctx.fillStyle = "#4b5563";
  ctx.font = "500 30px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
  ctx.fillText("实时价格监控 · 仅供参考", 88, 214);

  const updatedAt = latestUpdatedAt([goldPrice, silverPrice]);
  ctx.fillStyle = "#6b7280";
  ctx.font = "500 28px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
  ctx.fillText("更新时间 " + updatedAt.format("YYYY-MM-DD HH:mm"), 88, 280);

  drawPriceRow(ctx, "黄金 AU", goldPrice, 366, "#b45309");
  drawPriceRow(ctx, "白银 AG", silverPrice, 696, "#475569");

  roundRect(ctx, 84, 1068, 912, 160, 32);
  ctx.fillStyle = "rgba(17, 24, 39, 0.88)";
  ctx.fill();
  ctx.fillStyle = "#f9fafb";
  ctx.font = "700 34px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
  ctx.fillText("数据来源于公开市场，投资需自行判断", 132, 1138);
  ctx.fillStyle = "#d1d5db";
  ctx.font = "500 26px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
  ctx.fillText("由 Koen 的贵金属价格平台生成", 132, 1188);

  ctx.fillStyle = "#111827";
  ctx.font = "800 34px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
  ctx.fillText(SITE_URL, 84, 1326);
  ctx.fillStyle = "#6b7280";
  ctx.font = "500 24px system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
  ctx.fillText("保存图片后可分享到朋友圈 / 小红书", 84, 1370);

  return canvas.toDataURL("image/png");
}

async function dataUrlToFile(dataUrl: string) {
  const res = await fetch(dataUrl);
  const blob = await res.blob();
  return new File([blob], "au-price-" + dayjs().format("YYYYMMDD-HHmm") + ".png", {
    type: "image/png",
  });
}

export default function SharePriceCard({ goldPrice, silverPrice }: SharePriceCardProps) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canGenerate = Boolean(goldPrice || silverPrice);
  const updatedAt = useMemo(
    () => latestUpdatedAt([goldPrice, silverPrice]).format("MM-DD HH:mm"),
    [goldPrice, silverPrice]
  );

  const handleGenerate = () => {
    try {
      setError(null);
      setImageUrl(generateShareImage(goldPrice, silverPrice));
    } catch (err) {
      setError(err instanceof Error ? err.message : "图片生成失败");
    }
  };

  const handleDownload = () => {
    if (!imageUrl) return;
    const link = document.createElement("a");
    link.href = imageUrl;
    link.download = "au-price-" + dayjs().format("YYYYMMDD-HHmm") + ".png";
    link.click();
  };

  const handleNativeShare = async () => {
    if (!imageUrl || !navigator.share) {
      handleDownload();
      return;
    }
    const file = await dataUrlToFile(imageUrl);
    const shareData = {
      title: "今日金银价",
      text: "今日金银价来自 " + SITE_URL,
      files: [file],
    };
    if (navigator.canShare?.(shareData)) {
      await navigator.share(shareData);
    } else {
      handleDownload();
    }
  };

  return (
    <section className="mb-8 rounded-2xl border border-amber-100 dark:border-amber-900/40 bg-white dark:bg-gray-800 shadow-lg p-5 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-600 dark:text-amber-400">
            Share Card
          </p>
          <h2 className="mt-1 text-lg font-semibold text-gray-900 dark:text-white">
            分享今日金价
          </h2>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            生成带水印的金银价卡片，更新于 {updatedAt}
          </p>
        </div>
        <button
          type="button"
          onClick={handleGenerate}
          disabled={!canGenerate}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-amber-500 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-amber-600 disabled:cursor-not-allowed disabled:bg-gray-300 disabled:text-gray-500 dark:disabled:bg-gray-700"
        >
          <Share2 className="h-4 w-4" />
          生成分享图
        </button>
      </div>

      {error && (
        <p className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p>
      )}

      {imageUrl && (
        <div className="mt-5 grid gap-4 lg:grid-cols-[minmax(0,360px)_1fr] lg:items-start">
          <img
            src={imageUrl}
            alt="今日金价分享卡片预览"
            className="w-full max-w-[360px] rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 shadow-sm"
          />
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={handleDownload}
              className="inline-flex items-center gap-2 rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-700"
            >
              <Download className="h-4 w-4" />
              保存图片
            </button>
            <button
              type="button"
              onClick={handleNativeShare}
              className="inline-flex items-center gap-2 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-white"
            >
              <Share2 className="h-4 w-4" />
              系统分享
            </button>
            <button
              type="button"
              onClick={() => setImageUrl(null)}
              className="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-gray-500 transition hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
            >
              <X className="h-4 w-4" />
              关闭预览
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
