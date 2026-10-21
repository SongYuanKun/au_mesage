"""趋势与K线数据读取操作。"""

from typing import List, Dict

from db.base import BaseDB


class TrendReader(BaseDB):
    """趋势查询：ohlc / intraday / gold_silver_ratio / last_n_days"""

    def get_last_n_days_daily_price(self, data_type: str, start_date: str, end_date: str) -> List[Dict]:
        """获取日期范围内每天最后一条回收价格"""
        return self._exec("""
            SELECT trade_date AS date, recycle_price
            FROM (
                SELECT trade_date, recycle_price,
                       ROW_NUMBER() OVER(PARTITION BY trade_date ORDER BY created_at DESC) AS rn
                FROM price_data
                WHERE data_type = %s AND recycle_price > 0
                  AND trade_date >= %s AND trade_date <= %s
            ) sub WHERE rn = 1 ORDER BY date ASC
        """, (data_type, start_date, end_date))

    def get_ohlc_trend(self, data_type: str, start_date: str, end_date: str) -> List[Dict]:
        """获取日K线数据（开盘/最高/最低/收盘），窗口函数实现"""
        return self._exec("""
            SELECT trade_date AS date, open_price, high_price, low_price, close_price
            FROM (
                SELECT trade_date,
                       FIRST_VALUE(recycle_price) OVER w_asc  AS open_price,
                       MAX(recycle_price) OVER w_asc           AS high_price,
                       MIN(recycle_price) OVER w_asc           AS low_price,
                       FIRST_VALUE(recycle_price) OVER w_desc  AS close_price,
                       ROW_NUMBER() OVER w_asc                 AS rn
                FROM price_data
                WHERE data_type = %s AND recycle_price > 0
                  AND trade_date BETWEEN %s AND %s
                WINDOW w_asc  AS (PARTITION BY trade_date ORDER BY created_at ASC),
                       w_desc AS (PARTITION BY trade_date ORDER BY created_at DESC)
            ) sub WHERE rn = 1 ORDER BY date ASC
        """, (data_type, start_date, end_date))

    def get_intraday_trend(self, data_type: str, date_str: str) -> List[Dict]:
        """获取指定日期的分钟级别走势数据"""
        return self._exec("""
            SELECT trade_time AS time, recycle_price, real_time_price, created_at
            FROM price_data
            WHERE data_type = %s AND recycle_price > 0 AND trade_date = %s
            ORDER BY created_at ASC
        """, (data_type, date_str))

    def get_gold_silver_ratio(self, start_date: str, end_date: str) -> List[Dict]:
        """同一来源、币种与市场口径的金银比，避免国内/国际报价交叉相除。"""
        return self._exec("""
            WITH ranked AS (
                SELECT trade_date AS date, data_type, source, currency, recycle_price,
                       CASE
                         WHEN data_type = 'XAU' THEN 'gold'
                         WHEN data_type = 'XAG' THEN 'silver'
                         WHEN data_type = '黄 金' THEN 'gold'
                         WHEN data_type = '白 银' THEN 'silver'
                       END AS metal,
                       CASE WHEN data_type IN ('XAU', 'XAG') THEN 'international' ELSE 'domestic' END AS market,
                       ROW_NUMBER() OVER (
                         PARTITION BY trade_date, data_type, source, currency
                         ORDER BY created_at DESC
                       ) AS rn
                FROM price_data
                WHERE data_type IN ('黄 金', 'XAU', '白 银', 'XAG')
                  AND recycle_price > 0 AND trade_date BETWEEN %s AND %s
            )
            , paired AS (
                SELECT g.date, g.recycle_price AS gold_close, s.recycle_price AS silver_close,
                       ROUND(g.recycle_price / s.recycle_price, 2) AS ratio,
                       ROW_NUMBER() OVER (
                         PARTITION BY g.date
                         ORDER BY CASE g.market WHEN 'international' THEN 0 ELSE 1 END, g.source
                       ) AS pair_rank
                FROM ranked g
                JOIN ranked s ON g.date = s.date AND g.source = s.source
                             AND g.currency = s.currency AND g.market = s.market
                WHERE g.rn = 1 AND s.rn = 1 AND g.metal = 'gold' AND s.metal = 'silver'
            )
            SELECT date, gold_close, silver_close, ratio
            FROM paired WHERE pair_rank = 1
            ORDER BY date ASC
        """, (start_date, end_date))

    def get_daily_ohlc(self, data_type: str, source: str,
                       start_date: str, end_date: str, currency: str = None) -> List[Dict]:
        """查询 daily_ohlc 表中的日线数据"""
        query = ("SELECT trade_date AS date, open_price, high_price, low_price, close_price, "
                 "volume, currency, source FROM daily_ohlc "
                 "WHERE data_type = %s AND source = %s AND trade_date BETWEEN %s AND %s ")
        params = [data_type, source, start_date, end_date]
        if currency:
            query += " AND currency = %s"
            params.append(currency)
        query += " ORDER BY trade_date ASC"
        return self._exec(query, params)
