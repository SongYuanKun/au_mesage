"""
Fawazahmed0Collector — 对接 cdn.jsdelivr.net/@fawazahmed0/currency-api
免费、无需 API Key，提供 XAU/XAG 对 CNY/USD 的日收盘汇率
每日采集一次（数据为前一日收盘）
同时写入 daily_ohlc 表作为日线基准价
"""
import json
import logging
from urllib.request import Request, urlopen

from collectors.base import BaseCollector
from collectors.errors import CollectionError

logger = logging.getLogger(__name__)

BASE_URL = 'https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{symbol}.min.json'

SYMBOLS = [
    ('XAU', ['cny', 'usd']),
    ('XAG', ['cny', 'usd']),
]


class Fawazahmed0Collector(BaseCollector):
    name = 'fawazahmed0'
    interval = 86400  # 每天一次

    def fetch(self) -> list:
        date_str = self.today_str()
        successful_symbols = 0
        failed_symbols = []

        for symbol, target_currencies in SYMBOLS:
            try:
                url = BASE_URL.format(symbol=symbol.lower())
                req = Request(url, headers={'User-Agent': 'au-mesage/1.0'})
                with urlopen(req, timeout=15) as resp:
                    body = json.loads(resp.read().decode())
                symbol_data = body.get(symbol.lower(), {})
                api_date = body.get('date', date_str)
                parsed_rates = []
                for currency in target_currencies:
                    raw_rate = symbol_data.get(currency)
                    if raw_rate is None:
                        continue
                    price = float(raw_rate)
                    if price <= 0:
                        continue
                    parsed_rates.append((currency, price))
                if not parsed_rates:
                    raise ValueError('no positive target rate')
            except Exception as exc:
                failed_symbols.append(symbol)
                logger.warning('[%s] 获取 %s 失败: %s', self.name, symbol, exc)
                continue

            for currency, price in parsed_rates:
                self.mysql_manager.upsert_daily_ohlc(
                    trade_date=api_date,
                    data_type=symbol,
                    source=self.name,
                    currency=currency.upper(),
                    open_price=price,
                    high_price=price,
                    low_price=price,
                    close_price=price,
                )
            successful_symbols += 1
            logger.info(
                '[%s] %s 日线数据已写入，日期 %s',
                self.name,
                symbol,
                api_date,
            )

        if successful_symbols == 0:
            raise CollectionError(
                f"{self.name}: all upstream symbols failed "
                f"({','.join(failed_symbols)})"
            )
        return []
