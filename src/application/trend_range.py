"""趋势接口共用的日期区间解析（与路由中的错误文案保持一致）。"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional, Tuple

_OHLC_RANGE_DAYS = {"7d": 6, "30d": 29, "90d": 89, "1y": 364}


def _start_date_for_ohlc(range_str: str, today: date) -> Optional[str]:
    if range_str == "all":
        return "2000-01-01"
    if range_str in _OHLC_RANGE_DAYS:
        return (today - timedelta(days=_OHLC_RANGE_DAYS[range_str])).strftime("%Y-%m-%d")
    return None


def parse_range_for_price_trend_ohlc(range_str: str, today: date) -> Tuple[Optional[str], Optional[str]]:
    """返回 (start_date_str, error_message)。error 非空时与 api 原样一致。"""
    start = _start_date_for_ohlc(range_str, today)
    if start is None:
        return None, "无效的 range 参数，可选: 1d/7d/30d/90d/1y/all"
    return start, None


def parse_range_for_gold_silver_ratio(range_str: str, today: date) -> Tuple[Optional[str], Optional[str]]:
    start = _start_date_for_ohlc(range_str, today)
    if start is None:
        return None, "无效的 range 参数"
    return start, None
