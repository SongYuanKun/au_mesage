import logging
import os
import threading
from typing import Callable, Dict, Mapping, Optional

from collectors.base import BaseCollector
from collectors.exchange_rate import ExchangeRateCollector
from collectors.fawazahmed0 import Fawazahmed0Collector
from collectors.gold_api import GoldAPICollector
from collectors.source_config import source_config_cache

logger = logging.getLogger(__name__)

CollectorFactory = Callable[[], BaseCollector]


class CollectorManager:
    def __init__(
        self,
        mysql_manager,
        *,
        collector_factories: Optional[Mapping[str, CollectorFactory]] = None,
        config_cache=source_config_cache,
        reconcile_interval: float = 60,
    ):
        self.mysql_manager = mysql_manager
        self._config_cache = config_cache
        self._config_cache.bind_db(mysql_manager)
        factories = (
            collector_factories
            if collector_factories is not None
            else self._default_factories()
        )
        self._factories = dict(factories)
        self._reconcile_interval = reconcile_interval
        self._collectors: Dict[str, BaseCollector] = {}
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._reconcile_thread = None

    def _default_factories(self) -> Mapping[str, CollectorFactory]:
        def create_playwright():
            from collectors.playwright_collector import PlaywrightCollector

            return PlaywrightCollector(self.mysql_manager)

        return {
            "gold_api": lambda: GoldAPICollector(self.mysql_manager),
            "exchange_rate": lambda: ExchangeRateCollector(self.mysql_manager),
            "fawazahmed0": lambda: Fawazahmed0Collector(self.mysql_manager),
            "playwright": create_playwright,
        }

    @property
    def collectors(self) -> list:
        with self._lock:
            return list(self._collectors.values())

    def _desired_source_ids(self) -> set:
        rows = self._config_cache.refresh(force=True)
        desired = {
            row["source_id"]
            for row in rows
            if row.get("enabled") and row.get("source_id") in self._factories
        }
        if os.environ.get("ENABLE_PLAYWRIGHT", "true").lower() == "false":
            desired.discard("playwright")
        return desired

    def _reconcile_locked(self) -> None:
        desired = self._desired_source_ids()
        running = set(self._collectors)

        for source_id in sorted(running - desired):
            collector = self._collectors[source_id]
            try:
                collector.stop()
            except Exception:
                logger.exception("停止数据源 %s 失败，将在下一轮重试", source_id)
                continue
            del self._collectors[source_id]

        if self._stop_event.is_set():
            return

        for source_id in sorted(desired - set(self._collectors)):
            collector = None
            try:
                collector = self._factories[source_id]()
                collector.start()
            except Exception:
                logger.exception("启动数据源 %s 失败，将在下一轮重试", source_id)
                if collector is not None:
                    try:
                        collector.stop()
                    except Exception:
                        logger.exception("清理启动失败的数据源 %s 时再次失败", source_id)
                continue
            self._collectors[source_id] = collector

        logger.info(
            "运行中的采集器: %s",
            sorted(self._collectors),
        )

    def reconcile_once(self) -> None:
        with self._lock:
            if self._stop_event.is_set():
                return
            self._reconcile_locked()

    def _reconcile_loop(self) -> None:
        while not self._stop_event.wait(self._reconcile_interval):
            try:
                self.reconcile_once()
            except Exception:
                logger.exception("数据源运行集合对账失败")

    def start_all(self) -> None:
        with self._lock:
            if self._reconcile_thread is not None and self._reconcile_thread.is_alive():
                return
            self._stop_event.clear()
            self._reconcile_locked()
            thread = threading.Thread(
                target=self._reconcile_loop,
                name="collector-reconciler",
                daemon=True,
            )
            self._reconcile_thread = thread
            thread.start()

    def stop_all(self) -> None:
        self._stop_event.set()
        thread = self._reconcile_thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=20)

        with self._lock:
            for source_id in list(self._collectors):
                collector = self._collectors[source_id]
                try:
                    collector.stop()
                except Exception:
                    logger.exception("关闭数据源 %s 失败", source_id)
                    continue
                del self._collectors[source_id]
            if thread is None or not thread.is_alive():
                self._reconcile_thread = None
