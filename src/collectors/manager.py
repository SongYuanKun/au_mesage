"""
CollectorManager — 统一调度所有数据采集器
根据环境变量决定启用哪些采集器
"""
import logging
import os

from collectors.gold_api import GoldAPICollector
from collectors.exchange_rate import ExchangeRateCollector
from collectors.fawazahmed0 import Fawazahmed0Collector

logger = logging.getLogger(__name__)


class CollectorManager:
    def __init__(self, mysql_manager):
        self.mysql_manager = mysql_manager
        self.collectors = []
        self._setup()

    def _setup(self):
        # API 采集器：始终启用
        self.collectors.append(GoldAPICollector(self.mysql_manager))
        self.collectors.append(ExchangeRateCollector(self.mysql_manager))
        self.collectors.append(Fawazahmed0Collector(self.mysql_manager))

        # Playwright 采集器：通过环境变量控制，默认关闭
        if os.environ.get('ENABLE_PLAYWRIGHT', 'false').lower() == 'true':
            try:
                from collectors.playwright_collector import PlaywrightCollector
                self.collectors.append(PlaywrightCollector(self.mysql_manager))
                logger.info("Playwright 采集器已启用")
            except ImportError:
                logger.warning("playwright 未安装，跳过 Playwright 采集器")
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
