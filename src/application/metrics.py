from __future__ import annotations

from datetime import datetime
from math import ceil
from typing import Any


def _as_naive_datetime(v: Any) -> datetime | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.replace(tzinfo=None)
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        try:
            return datetime.fromisoformat(s).replace(tzinfo=None)
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
    return None


def _freshness_seconds(latest_at: Any, now: datetime) -> int | None:
    d = _as_naive_datetime(latest_at)
    if d is None:
        return None
    n = now.replace(tzinfo=None)
    sec = (n - d).total_seconds()
    if sec < 0:
        sec = 0
    return int(sec)


def _data_status(freshness: int | None) -> str:
    if freshness is None:
        return "abnormal"
    if freshness <= 120:
        return "normal"
    if freshness <= 600:
        return "delayed"
    return "abnormal"


def _p95(values: list[int]) -> int | None:
    if not values:
        return None
    vs = sorted(values)
    idx = max(0, min(len(vs) - 1, ceil(0.95 * len(vs)) - 1))
    return vs[idx]


def build_quality_metrics_payload(
    latest_updates: list[dict[str, Any]],
    counts_last_hour: list[dict[str, Any]],
    now: datetime,
    *,
    window_seconds: int = 3600,
    expected_interval_seconds: int = 60,
) -> dict[str, Any]:
    expected_count = max(1, int(window_seconds / expected_interval_seconds))

    cnt_map: dict[tuple[str, str], int] = {}
    for r in counts_last_hour:
        key = (str(r.get("data_type")), str(r.get("source")))
        cnt_map[key] = int(r.get("cnt_last_hour") or 0)

    groups: list[dict[str, Any]] = []
    freshness_values: list[int] = []

    for r in latest_updates:
        data_type = str(r.get("data_type"))
        source = str(r.get("source"))
        latest_at = r.get("latest_at")
        cnt = cnt_map.get((data_type, source), 0)

        freshness = _freshness_seconds(latest_at, now)
        if freshness is not None:
            freshness_values.append(freshness)

        missing_rate = max(0.0, 1.0 - (cnt / expected_count))
        groups.append(
            {
                "data_type": data_type,
                "source": source,
                "latest_at": str(latest_at or ""),
                "freshness_seconds": freshness,
                "data_status": _data_status(freshness),
                "count_last_hour": cnt,
                "expected_count_last_hour": expected_count,
                "missing_rate": round(missing_rate, 4),
                "collector_success_rate": round(min(1.0, cnt / expected_count), 4),
            }
        )

    groups.sort(key=lambda x: (x["data_type"], x["source"]))

    return {
        "success": True,
        "generated_at": now.isoformat(),
        "window_seconds": window_seconds,
        "expected_interval_seconds": expected_interval_seconds,
        "freshness_p95_seconds": _p95(freshness_values),
        "groups": groups,
    }

