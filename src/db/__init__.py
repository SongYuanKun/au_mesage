"""数据库管理门面类 — 组合连接池 + 子模块，对外保持统一接口。"""

from typing import Dict, List, Optional

from db.pool import ConnectionPool
from db.price_writer import PriceWriter
from db.price_reader import PriceReader
from db.trend_reader import TrendReader
from db.exchange_reader import ExchangeReader


class DatabaseManager:
    """
    组合式数据库管理器。
    - writer:  采集器写入操作 (price_data / exchange_rate / daily_ohlc)
    - reader:  价格查询操作 (overview / latest / history)
    - trend:   趋势查询操作 (ohlc / intraday / ratio)
    - exchange: 汇率查询操作
    所有方法通过委托暴露，保持 mysql_manager.xxx() 的调用方式。
    """

    def __init__(self, config: Dict):
        self.pool = ConnectionPool(config)
        self.writer = PriceWriter(self.pool)
        self.reader = PriceReader(self.pool)
        self.trend = TrendReader(self.pool)
        self.exchange = ExchangeReader(self.pool)

    # ── 写入委托 ──────────────────────────────────────────
    def batch_insert_data(self, data_list: List[Dict]):
        return self.writer.batch_insert_data(data_list)

    def upsert_exchange_rate(self, base: str, target: str, rate: float, source: str):
        return self.writer.upsert_exchange_rate(base, target, rate, source)

    def upsert_daily_ohlc(self, trade_date: str, data_type: str, source: str,
                          currency: str, open_price: float, high_price: float,
                          low_price: float, close_price: float, volume: float = None):
        return self.writer.upsert_daily_ohlc(
            trade_date, data_type, source, currency,
            open_price, high_price, low_price, close_price, volume)

    # ── 价格查询委托 ──────────────────────────────────────
    def query_data(self, start_date: str, end_date: str, data_type: Optional[str] = None):
        return self.reader.query_data(start_date, end_date, data_type)

    def get_latest_data_by_type(self):
        return self.reader.get_latest_data_by_type()

    def get_latest_data(self, data_type: Optional[str] = None) -> Optional[Dict]:
        return self.reader.get_latest_data(data_type)

    def get_price_history(self, data_type: str, limit: int = 20) -> List[Dict]:
        return self.reader.get_price_history(data_type, limit)

    def get_latest_market_price(self, data_type: str) -> Optional[float]:
        return self.reader.get_latest_market_price(data_type)

    def get_daily_history(self, date: str, data_type: Optional[str] = None) -> List[Dict]:
        return self.reader.get_daily_history(date, data_type)

    def get_price_overview_data(self, today_str: str, yesterday_str: str) -> List[Dict]:
        return self.reader.get_price_overview_data(today_str, yesterday_str)

    def get_price_history_by_time_range(self, data_type: str, start_time: str, end_time: str) -> List[Dict]:
        return self.reader.get_price_history_by_time_range(data_type, start_time, end_time)

    # ── 趋势查询委托 ──────────────────────────────────────
    def get_last_n_days_daily_price(self, data_type: str, start_date: str, end_date: str) -> List[Dict]:
        return self.trend.get_last_n_days_daily_price(data_type, start_date, end_date)

    def get_ohlc_trend(self, data_type: str, start_date: str, end_date: str) -> List[Dict]:
        return self.trend.get_ohlc_trend(data_type, start_date, end_date)

    def get_intraday_trend(self, data_type: str, date_str: str) -> List[Dict]:
        return self.trend.get_intraday_trend(data_type, date_str)

    def get_gold_silver_ratio(self, start_date: str, end_date: str) -> List[Dict]:
        return self.trend.get_gold_silver_ratio(start_date, end_date)

    def get_daily_ohlc(self, data_type: str, source: str,
                       start_date: str, end_date: str, currency: str = None) -> List[Dict]:
        return self.trend.get_daily_ohlc(data_type, source, start_date, end_date, currency)

    # ── 汇率查询委托 ──────────────────────────────────────
    def get_latest_exchange_rate(self, base: str, target: str) -> Optional[float]:
        return self.exchange.get_latest_exchange_rate(base, target)
