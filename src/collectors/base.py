"""
BaseCollector — 所有数据采集器的抽象基类
"""
import logging
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime

import pytz

from collectors import stats as collector_stats

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
        if self.is_running:
            return
        if self._thread is not None and self._thread.is_alive():
            raise RuntimeError(f"[{self.name}] 上一个采集线程仍在运行")
        self.is_running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"[{self.name}] 采集器已启动，间隔 {self.interval}s")

    def stop(self, join_timeout: float = 20.0):
        self.is_running = False
        thread = self._thread
        if thread is threading.current_thread():
            raise RuntimeError(f"[{self.name}] 采集线程不能等待自身退出")
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=join_timeout)
            if thread.is_alive():
                raise RuntimeError(f"[{self.name}] 采集线程未在 {join_timeout}s 内退出")
        self._thread = None
        logger.info(f"[{self.name}] 采集器已停止")

    def is_alive(self) -> bool:
        """采集线程是否仍在运行；管理器据此重新拉起意外退出的采集器。"""
        return self._thread is not None and self._thread.is_alive()

    def _run(self):
        consecutive_failures = 0
        max_backoff = 3600  # 最大退避 1 小时
        failure_threshold = 5

        while self.is_running:
            started = time.monotonic()
            try:
                data = self.fetch()
                if data:
                    self.mysql_manager.batch_insert_data(data)
                    logger.info(f"[{self.name}] 写入 {len(data)} 条数据")

                latency_ms = (time.monotonic() - started) * 1000.0
                collector_stats.record_success(self.name, latency_ms)
                if consecutive_failures > 0:
                    logger.info(f"[{self.name}] 采集器恢复正常")
                consecutive_failures = 0
            except Exception as e:
                collector_stats.record_failure(self.name)
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
