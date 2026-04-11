"""健康检查响应体（无 Flask）。"""

from __future__ import annotations

from typing import Any, Dict


def build_health_payload(timestamp_iso: str) -> Dict[str, Any]:
    """对应 GET /api/health 成功 JSON。"""
    return {
        "status": "healthy",
        "timestamp": timestamp_iso,
        "service": "price-data-api",
    }
