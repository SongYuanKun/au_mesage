"""数据源配置加载（DB + 60s 缓存）。"""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_SOURCES: list[dict[str, Any]] = [
    {"source_id": "gold_api", "enabled": True, "priority": 10},
    {"source_id": "fawazahmed0", "enabled": True, "priority": 20},
    {"source_id": "exchange_rate", "enabled": True, "priority": 30},
    {"source_id": "playwright", "enabled": True, "priority": 40},
]

_CACHE_TTL_SECONDS = 60


class SourceConfigCache:
    def __init__(self) -> None:
        self._items: list[dict[str, Any]] = list(DEFAULT_SOURCES)
        self._loaded_at: float = 0.0
        self._db: Any = None

    def bind_db(self, mysql_manager: Any) -> None:
        self._db = mysql_manager

    def refresh(self, force: bool = False) -> list[dict[str, Any]]:
        now = time.monotonic()
        if not force and (now - self._loaded_at) < _CACHE_TTL_SECONDS:
            return list(self._items)

        if self._db is None:
            self._items = list(DEFAULT_SOURCES)
            self._loaded_at = now
            return list(self._items)

        try:
            rows = self._db.list_data_source_configs()
            if rows:
                self._items = rows
            else:
                self._db.seed_data_source_configs(DEFAULT_SOURCES, changed_by="system")
                self._items = self._db.list_data_source_configs() or list(DEFAULT_SOURCES)
        except Exception:
            logger.exception("加载数据源配置失败，使用默认配置")
            self._items = list(DEFAULT_SOURCES)

        self._loaded_at = now
        return list(self._items)

    def is_enabled(self, source_id: str) -> bool:
        for row in self.refresh():
            if row.get("source_id") == source_id:
                return bool(row.get("enabled"))
        return True

    def invalidate(self) -> None:
        self._loaded_at = 0.0


source_config_cache = SourceConfigCache()
