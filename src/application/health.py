"""健康检查响应体（无 Flask）。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable


def _as_datetime(value: Any, *, default_tz=timezone.utc) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    elif not isinstance(value, datetime):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=default_tz)
    return parsed.astimezone(timezone.utc)


def build_health_payload(
    timestamp_iso: str,
    *,
    database_ok: bool,
    latest_updates: Iterable[Dict[str, Any]] | None = None,
    max_data_age_seconds: int = 600,
    future_tolerance_seconds: int = 60,
) -> Dict[str, Any]:
    """构造 readiness 响应：数据库可读且至少有一条新鲜价格才可接流量。"""
    timestamp = datetime.fromisoformat(timestamp_iso.replace("Z", "+00:00"))
    default_tz = timestamp.tzinfo or timezone.utc
    now = _as_datetime(timestamp_iso, default_tz=default_tz)
    freshest_seconds = None
    future_data = False
    if now is not None:
        ages = []
        for row in latest_updates or []:
            latest_at = _as_datetime(row.get("latest_at"), default_tz=default_tz)
            if latest_at is not None:
                age = (now - latest_at).total_seconds()
                if age < -future_tolerance_seconds:
                    future_data = True
                    continue
                ages.append(max(0, int(age)))
        if ages:
            freshest_seconds = min(ages)

    ready = bool(database_ok and freshest_seconds is not None and freshest_seconds <= max_data_age_seconds)
    reason = None
    if not database_ok:
        reason = "database_unavailable"
    elif freshest_seconds is None and future_data:
        reason = "price_data_future"
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
            "price_data": "fresh" if ready else ("future" if future_data and freshest_seconds is None else ("unavailable" if freshest_seconds is None else "stale")),
            "freshest_data_age_seconds": freshest_seconds,
            "max_data_age_seconds": max_data_age_seconds,
        },
        "reason": reason,
    }
