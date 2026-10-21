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

_STATE_IDLE = "idle"
_STATE_RUNNING = "running"
_STATE_STOPPING = "stopping"
_STATE_STOPPED = "stopped"


class CollectorManager:
    def __init__(
        self,
        mysql_manager,
        *,
        collector_factories: Optional[Mapping[str, CollectorFactory]] = None,
        config_cache=source_config_cache,
        reconcile_interval: float = 30,
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
        # 依赖未安装的数据源：进程内不再重复导入，避免每轮调和刷异常栈
        self._unavailable: set = set()
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._reconcile_thread = None
        self._generation = 0
        self._lifecycle_state = _STATE_IDLE

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

    def _desired_source_ids(self) -> list[str]:
        rows = self._config_cache.refresh(force=True)
        desired = [
            row["source_id"]
            for row in sorted(rows, key=lambda row: (int(row.get("priority", 100)), row.get("source_id", "")))
            if row.get("enabled") and row.get("source_id") in self._factories
        ]
        if os.environ.get("ENABLE_PLAYWRIGHT", "true").lower() == "false":
            desired = [source_id for source_id in desired if source_id != "playwright"]
        return desired

    def _reconcile_locked(self, stop_event=None) -> None:
        # 线程已退出的实例（启动后崩溃、停止超时后才退出等）先清理，下面按配置重新拉起
        for source_id in sorted(self._collectors):
            collector = self._collectors[source_id]
            if collector.is_alive():
                continue
            try:
                collector.stop()
            except Exception:
                logger.exception("清理已退出的数据源 %s 失败，将在下一轮重试", source_id)
                continue
            del self._collectors[source_id]
            logger.warning("数据源 %s 的采集线程已退出，按配置重新调和", source_id)

        desired_ids = self._desired_source_ids()
        desired = set(desired_ids)
        running = set(self._collectors)

        for source_id in sorted(running - desired):
            collector = self._collectors[source_id]
            try:
                collector.stop()
            except Exception:
                logger.exception("停止数据源 %s 失败，将在下一轮重试", source_id)
                continue
            del self._collectors[source_id]

        if stop_event is not None and stop_event.is_set():
            return

        for source_id in desired_ids:
            if source_id in self._collectors or source_id in self._unavailable:
                continue
            collector = None
            try:
                collector = self._factories[source_id]()
                collector.start()
            except ImportError as e:
                logger.warning("数据源 %s 依赖未安装，本进程内不再启动: %s", source_id, e)
                self._unavailable.add(source_id)
                continue
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
            if self._lifecycle_state in {_STATE_STOPPING, _STATE_STOPPED}:
                return
            self._reconcile_locked(self._stop_event)

    def _reconcile_loop(self, generation=None, stop_event=None) -> None:
        if generation is None:
            generation = self._generation
        if stop_event is None:
            stop_event = self._stop_event
        if stop_event is None:
            return

        while not stop_event.wait(self._reconcile_interval):
            try:
                with self._lock:
                    if (
                        self._lifecycle_state != _STATE_RUNNING
                        or self._generation != generation
                        or self._stop_event is not stop_event
                    ):
                        return
                    self._reconcile_locked(stop_event)
            except Exception:
                logger.exception("数据源运行集合对账失败")

    def start_all(self) -> None:
        with self._lock:
            if self._lifecycle_state == _STATE_STOPPING:
                return
            if (
                self._lifecycle_state == _STATE_RUNNING
                and self._reconcile_thread is not None
                and self._reconcile_thread.is_alive()
            ):
                return

            # A generation owns an immutable stop signal. A later generation
            # replaces the signal instead of clearing one an older thread sees.
            if self._stop_event is not None:
                self._stop_event.set()
            self._generation += 1
            generation = self._generation
            stop_event = threading.Event()
            self._stop_event = stop_event
            self._lifecycle_state = _STATE_RUNNING
            try:
                self._reconcile_locked(stop_event)
            except Exception:
                stop_event.set()
                self._stop_event = None
                self._lifecycle_state = _STATE_STOPPED
                raise

            thread = threading.Thread(
                target=self._reconcile_loop,
                args=(generation, stop_event),
                name="collector-reconciler",
                daemon=True,
            )
            self._reconcile_thread = thread
            thread.start()

    def stop_all(self) -> None:
        with self._lock:
            self._lifecycle_state = _STATE_STOPPING
            generation = self._generation
            stop_event = self._stop_event
            thread = self._reconcile_thread
            if stop_event is not None:
                stop_event.set()

        if thread is threading.current_thread():
            raise RuntimeError("对账线程不能停止其自身")
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=20)
            if thread.is_alive():
                raise RuntimeError("对账线程未在 20s 内退出")

        with self._lock:
            for source_id in list(self._collectors):
                collector = self._collectors[source_id]
                try:
                    collector.stop()
                except Exception:
                    logger.exception("关闭数据源 %s 失败", source_id)
                    continue
                del self._collectors[source_id]

            if (
                self._generation == generation
                and self._reconcile_thread is thread
                and self._stop_event is stop_event
            ):
                self._reconcile_thread = None
                self._stop_event = None
                self._lifecycle_state = _STATE_STOPPED
