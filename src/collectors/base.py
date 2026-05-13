"""
BaseCollector — 所有数据采集器的抽象基类
"""
import logging
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime

import pytz

BEIJING_TZ = pytz.timezone('Asia/Shanghai')
logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    name: str = 'base'
    interval: int = 60  # 采集间隔（秒）

    def __init__(self, mysql_manager):
        self.mysql_manager = mysql_manager
        self.is_running = False
        self._thread = None

    @abstractmethod
    def fetch(self) -> list:
        """
        采集数据，返回标准化的 dict 列表，格式：
        {
            'trade_date': 'YYYY-MM-DD',
            'trade_time': 'HH:MM:SS',
            'data_type': str,
            'real_time_price': float,
            'recycle_price': float,
            'high_price': float,
            'low_price': float,
            'source': str,
            'currency': str,   # 'CNY' or 'USD'
        }
        """

    def start(self):
        self.is_running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"[{self.name}] 采集器已启动，间隔 {self.interval}s")

    def stop(self):
        self.is_running = False
        logger.info(f"[{self.name}] 采集器已停止")

    def _run(self):
        consecutive_failures = 0
        max_backoff = 3600  # 最大退避 1 小时
        failure_threshold = 5

        while self.is_running:
            try:
                data = self.fetch()
                if data:
                    self.mysql_manager.batch_insert_data(data)
                    logger.info(f"[{self.name}] 写入 {len(data)} 条数据")
                
                if consecutive_failures > 0:
                    logger.info(f"[{self.name}] 采集器恢复正常")
                consecutive_failures = 0
            except Exception as e:
                consecutive_failures += 1
                logger.error(f"[{self.name}] 采集异常 (连续失败 {consecutive_failures} 次): {e}")
                if consecutive_failures == failure_threshold:
                    logger.error(f"[{self.name}] 达到失败阈值，采集器进入降级状态！")
            
            if consecutive_failures > 0:
                current_sleep = min(max_backoff, self.interval * (2 ** (consecutive_failures - 1)))
                logger.info(f"[{self.name}] 退避重试，休眠 {current_sleep}s ...")
            else:
                current_sleep = self.interval
            
            slept = 0
            while slept < current_sleep and self.is_running:
                time.sleep(1)
                slept += 1

    @staticmethod
    def now_beijing():
        return datetime.now(BEIJING_TZ)

    @staticmethod
    def today_str():
        return datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')

    @staticmethod
    def time_str():
        return datetime.now(BEIJING_TZ).strftime('%H:%M:%S')
