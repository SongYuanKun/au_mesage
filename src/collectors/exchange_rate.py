"""
ExchangeRateCollector — 对接 open.er-api.com
免费、无需 API Key，获取 USD/CNY 等主要汇率
更新频率：1 小时（汇率变动慢，无需频繁）
写入 exchange_rate 表，同时更新 price_data 换算值
"""
import json
import logging
import threading
from urllib.request import Request, urlopen
from urllib.error import URLError

from collectors.base import BaseCollector

logger = logging.getLogger(__name__)

BASE_URL = 'https://open.er-api.com/v6/latest/USD'

# 线程安全的最新汇率缓存，供其他模块读取
_rate_cache = {'USD_CNY': None, 'lock': threading.Lock()}


def get_usd_cny_rate() -> float | None:
    """获取最新 USD/CNY 汇率缓存（供其他采集器使用）"""
    with _rate_cache['lock']:
        return _rate_cache['USD_CNY']


class ExchangeRateCollector(BaseCollector):
    name = 'exchange_rate'
    interval = 3600  # 1 小时

    def fetch(self) -> list:
        try:
            req = Request(BASE_URL, headers={'User-Agent': 'au-mesage/1.0'})
            with urlopen(req, timeout=10) as resp:
                body = json.loads(resp.read().decode())

            if body.get('result') != 'success':
                logger.warning(f"[{self.name}] API 返回非成功状态: {body.get('result')}")
                return []

            rates = body.get('rates', {})
            cny_rate = rates.get('CNY')
            if not cny_rate:
                return []

            # 更新内存缓存
            with _rate_cache['lock']:
                _rate_cache['USD_CNY'] = float(cny_rate)

            # 写入 exchange_rate 表
            self.mysql_manager.upsert_exchange_rate('USD', 'CNY', float(cny_rate), self.name)
            logger.info(f"[{self.name}] USD/CNY = {cny_rate}")

        except (URLError, Exception) as e:
            logger.warning(f"[{self.name}] 汇率获取失败: {e}")

        # 不写 price_data，返回空列表
        return []
