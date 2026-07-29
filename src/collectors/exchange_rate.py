"""
ExchangeRateCollector — 对接 open.er-api.com
免费、无需 API Key，获取 USD/CNY 等主要汇率
更新频率：1 小时（汇率变动慢，无需频繁）
写入 exchange_rate 表，同时更新 price_data 换算值
"""
from __future__ import annotations

import json
import logging
import threading
from urllib.request import Request, urlopen

from collectors.base import BaseCollector
from collectors.errors import CollectionError

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
                raise ValueError(f"unexpected result: {body.get('result')}")
            cny_rate = float(body.get('rates', {}).get('CNY', 0))
            if cny_rate <= 0:
                raise ValueError('CNY rate must be positive')
        except Exception as exc:
            raise CollectionError(f'{self.name}: rate request failed') from exc

        self.mysql_manager.upsert_exchange_rate(
            'USD',
            'CNY',
            cny_rate,
            self.name,
        )
        with _rate_cache['lock']:
            _rate_cache['USD_CNY'] = cny_rate
        logger.info('[%s] USD/CNY = %s', self.name, cny_rate)
        return []
