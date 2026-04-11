"""
线程安全的简单 TTL 缓存。

用于热点只读 API 的短期响应缓存；多进程部署时各进程独立，不保证跨实例一致。
"""

from __future__ import annotations

import threading
import time
from typing import Any, Optional


class TtlCache:
    """键值 + 写入时间戳；get 时若未过期则返回值，否则返回 None。"""

    __slots__ = ("_data", "_lock")

    def __init__(self) -> None:
        self._data: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()

    def get(self, key: str, ttl: float = 10.0) -> Optional[Any]:
        """若存在且未超过 ttl（秒），返回缓存值；否则返回 None。"""
        with self._lock:
            entry = self._data.get(key)
            if entry and (time.time() - entry[1]) < ttl:
                return entry[0]
        return None

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = (value, time.time())

    def clear(self) -> None:
        """清空全部条目（供测试或运维重置进程内缓存）。"""
        with self._lock:
            self._data.clear()
