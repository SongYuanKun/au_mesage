"""
GoldAPICollector — 对接 api.gold-api.com
免费、无需 API Key，提供 XAU/XAG/XPT/XPD 实时 USD 现货价
更新频率：60 秒
"""
import json
import logging
from urllib.request import Request, urlopen

from collectors.base import BaseCollector
from collectors.errors import CollectionError
from collectors.validation import parse_positive_finite

logger = logging.getLogger(__name__)

# 采集的品种：(data_type标识, symbol)
SYMBOLS = [
    ('XAU', 'XAU'),   # 黄金
    ('XAG', 'XAG'),   # 白银
    ('XPT', 'XPT'),   # 铂金
    ('XPD', 'XPD'),   # 钯金
]

BASE_URL = 'https://api.gold-api.com/price/{symbol}'


class GoldAPICollector(BaseCollector):
    name = 'gold_api'
    interval = 60

    def fetch(self) -> list:
        results = []
        failures = []
        date_str = self.today_str()
        time_str = self.time_str()

        for data_type, symbol in SYMBOLS:
            try:
                url = BASE_URL.format(symbol=symbol)
                req = Request(url, headers={'User-Agent': 'au-mesage/1.0'})
                with urlopen(req, timeout=10) as resp:
                    body = json.loads(resp.read().decode())
                price = parse_positive_finite(body.get('price', 0))
                results.append({
                    'trade_date': date_str,
                    'trade_time': time_str,
                    'data_type': data_type,
                    'real_time_price': price,
                    'recycle_price': price,   # spot 无买卖价差，视为相同
                    'high_price': 0,
                    'low_price': 0,
                    'source': self.name,
                    'currency': 'USD',
                })
            except Exception as exc:
                failures.append(symbol)
                logger.warning('[%s] 获取 %s 失败: %s', self.name, symbol, exc)

        if not results:
            raise CollectionError(
                f"{self.name}: all upstream symbols failed ({','.join(failures)})"
            )
        return results
