"""
Fawazahmed0Collector — 对接 cdn.jsdelivr.net/@fawazahmed0/currency-api
免费、无需 API Key，提供 XAU/XAG 对 CNY/USD 的日收盘汇率
每日采集一次（数据为前一日收盘）
同时写入 daily_ohlc 表作为日线基准价
"""
import json
import logging
from urllib.request import Request, urlopen
from urllib.error import URLError

from collectors.base import BaseCollector

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
        rows_price_data = []

        for symbol, target_currencies in SYMBOLS:
            try:
                url = BASE_URL.format(symbol=symbol.lower())
                req = Request(url, headers={'User-Agent': 'au-mesage/1.0'})
                with urlopen(req, timeout=15) as resp:
                    body = json.loads(resp.read().decode())

                symbol_data = body.get(symbol.lower(), {})
                api_date = body.get('date', date_str)

                for currency in target_currencies:
                    rate = symbol_data.get(currency)
                    if not rate:
                        continue
                    price = float(rate)

                    # 写入 daily_ohlc 表（日线基准）
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

                    # CNY 价格也写入 price_data，与国内数据统一查询
                    if currency == 'cny':
                        rows_price_data.append({
                            'trade_date': api_date,
                            'trade_time': '00:00:00',
                            'data_type': symbol,
                            'real_time_price': price,
                            'recycle_price': price,
                            'high_price': 0,
                            'low_price': 0,
                            'source': self.name,
                            'currency': 'CNY',
                        })

                logger.info(f"[{self.name}] {symbol} 日线数据已写入，日期 {api_date}")

            except (URLError, Exception) as e:
                logger.warning(f"[{self.name}] 获取 {symbol} 失败: {e}")

        return rows_price_data
