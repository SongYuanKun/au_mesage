"""健康检查响应体（无 Flask）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable


def _as_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None
    return None


def build_health_payload(
    timestamp_iso: str,
    *,
    database_ok: bool,
    latest_updates: Iterable[Dict[str, Any]] | None = None,
    max_data_age_seconds: int = 600,
) -> Dict[str, Any]:
    """构造 readiness 响应：数据库可读且至少有一条新鲜价格才可接流量。"""
    now = _as_datetime(timestamp_iso)
    freshest_seconds = None
    if now is not None:
        ages = []
        for row in latest_updates or []:
            latest_at = _as_datetime(row.get("latest_at"))
            if latest_at is not None:
                ages.append(max(0, int((now - latest_at).total_seconds())))
        if ages:
            freshest_seconds = min(ages)

    ready = bool(database_ok and freshest_seconds is not None and freshest_seconds <= max_data_age_seconds)
    reason = None
    if not database_ok:
        reason = "database_unavailable"
    elif freshest_seconds is None:
        reason = "price_data_unavailable"
    elif freshest_seconds > max_data_age_seconds:
        reason = "price_data_stale"
    return {
        "status": "healthy" if ready else "unhealthy",
        "ready": ready,
        "timestamp": timestamp_iso,
        "service": "price-data-api",
        "checks": {
            "database": "ok" if database_ok else "unavailable",
            "price_data": "fresh" if ready else ("unavailable" if freshest_seconds is None else "stale"),
            "freshest_data_age_seconds": freshest_seconds,
            "max_data_age_seconds": max_data_age_seconds,
        },
        "reason": reason,
    }
