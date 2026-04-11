"""价格相关 API 的响应体组装（无 Flask、无 IO）。"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional


def build_price_overview_payload(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """对应 GET /api/price-overview 成功体中的 data 与外层 success。"""
    result: List[Dict[str, Any]] = []
    for r in rows:
        recycle = float(r.get("recycle_price", 0) or 0)
        yest = float(r["yesterday_close"]) if r.get("yesterday_close") is not None else None
        change = round(recycle - yest, 2) if yest is not None else None
        change_pct = round((change / yest) * 100, 2) if yest and yest != 0 else None
        result.append(
            {
                "data_type": r["data_type"],
                "recycle_price": recycle,
                "real_time_price": float(r.get("real_time_price", 0) or 0),
                "yesterday_close": yest,
                "change": change,
                "change_pct": change_pct,
                "today_high": float(r.get("today_high", 0) or 0),
                "today_low": float(r.get("today_low", 0) or 0),
                "updated_at": str(r.get("updated_at", "")),
            }
        )
    return {"success": True, "data": result}


def build_last_7_days_payload(
    rows: List[Dict[str, Any]],
    today: date,
) -> Dict[str, Any]:
    """近 7 日每日回收价：与原先循环逻辑一致（含缺失日为 None）。"""
    price_map = {str(r["date"]): float(r["recycle_price"] or 0) for r in rows}
    results: List[Dict[str, Any]] = []
    for i in range(6, -1, -1):
        day_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        price: Optional[float] = price_map.get(day_str)
        results.append({"date": day_str, "recycle_price": price})
    return {"success": True, "data": results}


def intraday_rows_to_line_series(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """1d 分钟线序列。"""
    data: List[Dict[str, Any]] = []
    for r in rows:
        rp = r.get("recycle_price")
        rt = r.get("real_time_price")
        frp = float(rp) if rp is not None else None
        frt = float(rt) if rt is not None else None
        data.append(
            {
                "time": str(r.get("time", "")),
                "price": frp if frp is not None else frt,
                "recycle_price": frp,
                "real_time_price": frt,
                "created_at": str(r.get("created_at", "")),
            }
        )
    return data


def ohlc_rows_to_candlestick_series(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """日 K OHLC 序列。"""
    data: List[Dict[str, Any]] = []
    for r in rows:
        data.append(
            {
                "date": str(r["date"]),
                "open": float(r["open_price"]) if r.get("open_price") else None,
                "high": float(r["high_price"]) if r.get("high_price") else None,
                "low": float(r["low_price"]) if r.get("low_price") else None,
                "close": float(r["close_price"]) if r.get("close_price") else None,
            }
        )
    return data


def build_price_trend_line_response(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"success": True, "range": "1d", "chart_type": "line", "data": data}


def build_price_trend_candlestick_response(range_str: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"success": True, "range": range_str, "chart_type": "candlestick", "data": data}


def gs_ratio_rows_to_series(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = []
    for r in rows:
        data.append(
            {
                "date": str(r["date"]),
                "ratio": float(r["ratio"]) if r.get("ratio") else None,
                "gold_close": float(r["gold_close"]) if r.get("gold_close") else None,
                "silver_close": float(r["silver_close"]) if r.get("silver_close") else None,
            }
        )
    return data


def build_gold_silver_ratio_payload(range_str: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    data = gs_ratio_rows_to_series(rows)
    ratios = [d["ratio"] for d in data if d["ratio"] is not None]
    stats: Dict[str, Any] = {}
    if ratios:
        stats = {
            "current": ratios[-1],
            "avg": round(sum(ratios) / len(ratios), 2),
            "max": max(ratios),
            "min": min(ratios),
        }
    return {"success": True, "range": range_str, "data": data, "stats": stats}
