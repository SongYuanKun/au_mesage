"""采集器运行状态（内存），供管理端查看健康度。"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Any

from collectors.base import BEIJING_TZ

_lock = threading.Lock()
_stats: dict[str, dict[str, Any]] = {}


def record_success(name: str, latency_ms: float) -> None:
    now = datetime.now(BEIJING_TZ).isoformat()
    with _lock:
        row = _stats.setdefault(
            name,
            {
                "source_id": name,
                "last_success_at": None,
                "last_failure_at": None,
                "failure_count": 0,
                "last_latency_ms": None,
            },
        )
        row["last_success_at"] = now
        row["last_latency_ms"] = round(latency_ms, 2)
        row["failure_count"] = 0


def record_failure(name: str) -> None:
    now = datetime.now(BEIJING_TZ).isoformat()
    with _lock:
        row = _stats.setdefault(
            name,
            {
                "source_id": name,
                "last_success_at": None,
                "last_failure_at": None,
                "failure_count": 0,
                "last_latency_ms": None,
            },
        )
        row["last_failure_at"] = now
        row["failure_count"] = int(row.get("failure_count") or 0) + 1


def snapshot() -> list[dict[str, Any]]:
    with _lock:
        return [dict(v) for v in _stats.values()]


def reset_for_tests() -> None:
    with _lock:
        _stats.clear()
