"""汇率解析：与「先 USD/CNY 内存缓存，未命中再查库」顺序一致（无 Flask）。"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

GetDbRate = Callable[[], Optional[float]]


def apply_usd_cny_cache_then_db(
    base: str,
    target: str,
    cached_usd_cny: Optional[float],
    get_db_rate: GetDbRate,
) -> Optional[float]:
    """
    仅当 base/target 为 USD/CNY 时使用 cached_usd_cny；
    若最终仍为 None，则调用 get_db_rate()（与原先短路逻辑一致，缓存命中时不访问 DB）。
    """
    rate: Optional[float] = None
    if base == "USD" and target == "CNY":
        rate = cached_usd_cny
    if rate is None:
        rate = get_db_rate()
    return rate


def build_exchange_rate_success_payload(
    base: str,
    target: str,
    rate: Any,
    updated_at_iso: str,
) -> Dict[str, Any]:
    """对应 GET /api/exchange-rate 成功 JSON。"""
    return {
        "success": True,
        "base": base,
        "target": target,
        "rate": rate,
        "updated_at": updated_at_iso,
    }
