"""
CollectorManager — 统一调度所有数据采集器
根据环境变量决定启用哪些采集器
"""
import logging
import os

from collectors.gold_api import GoldAPICollector
from collectors.exchange_rate import ExchangeRateCollector
from collectors.fawazahmed0 import Fawazahmed0Collector
from collectors.source_config import source_config_cache

logger = logging.getLogger(__name__)


class CollectorManager:
    def __init__(self, mysql_manager):
        self.mysql_manager = mysql_manager
        self.collectors = []
        source_config_cache.bind_db(mysql_manager)
        self._setup()

    def _setup(self):
        source_config_cache.refresh(force=True)
        candidates = [
            ("gold_api", lambda: GoldAPICollector(self.mysql_manager)),
            ("exchange_rate", lambda: ExchangeRateCollector(self.mysql_manager)),
            ("fawazahmed0", lambda: Fawazahmed0Collector(self.mysql_manager)),
        ]

        for source_id, factory in candidates:
            if source_config_cache.is_enabled(source_id):
                self.collectors.append(factory())
            else:
                logger.info("数据源 %s 已在配置中禁用，跳过采集器", source_id)

        playwright_enabled = source_config_cache.is_enabled("playwright")
        if playwright_enabled and os.environ.get("ENABLE_PLAYWRIGHT", "true").lower() != "false":
            try:
                from collectors.playwright_collector import PlaywrightCollector

                self.collectors.append(PlaywrightCollector(self.mysql_manager))
                logger.info("Playwright 采集器已启用")
            except ImportError:
                logger.warning("playwright 未安装，跳过 Playwright 采集器")
        elif not playwright_enabled:
            logger.info("Playwright 采集器已禁用（data_source_config）")
        else:
            logger.info("Playwright 采集器已禁用（ENABLE_PLAYWRIGHT=false）")

        logger.info(f"共启用 {len(self.collectors)} 个采集器: "
                    f"{[c.name for c in self.collectors]}")

    def start_all(self):
        for c in self.collectors:
            c.start()

    def stop_all(self):
        for c in self.collectors:
            c.stop()
