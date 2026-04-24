"""趋势与K线数据读取操作。"""

import logging
from typing import List, Dict, Optional

from mysql.connector import Error

from db.pool import ConnectionPool


class TrendReader:
    """趋势查询：ohlc / intraday / gold_silver_ratio / last_n_days"""

    def __init__(self, pool: ConnectionPool):
        self.pool = pool

    def _exec(self, query, params=None):
        """执行查询并自动归还连接。"""
        conn = None
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Error as e:
            logging.error(f"趋势查询失败: {e}")
            return []
        finally:
            if conn:
                conn.close()

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
        """获取金银比走势数据，兼容'黄 金'/'XAU'和'白 银'/'XAG'"""
        return self._exec("""
            SELECT g.date, g.close_price AS gold_close, s.close_price AS silver_close,
                   ROUND(g.close_price / s.close_price, 2) AS ratio
            FROM (
                SELECT trade_date AS date,
                       FIRST_VALUE(recycle_price) OVER w AS close_price,
                       ROW_NUMBER() OVER w AS rn
                FROM price_data
                WHERE data_type IN ('黄 金', 'XAU') AND recycle_price > 0
                  AND trade_date BETWEEN %s AND %s
                WINDOW w AS (PARTITION BY trade_date ORDER BY created_at DESC)
            ) g
            JOIN (
                SELECT trade_date AS date,
                       FIRST_VALUE(recycle_price) OVER w AS close_price,
                       ROW_NUMBER() OVER w AS rn
                FROM price_data
                WHERE data_type IN ('白 银', 'XAG') AND recycle_price > 0
                  AND trade_date BETWEEN %s AND %s
                WINDOW w AS (PARTITION BY trade_date ORDER BY created_at DESC)
            ) s ON g.date = s.date
            WHERE g.rn = 1 AND s.rn = 1
            ORDER BY g.date ASC
        """, (start_date, end_date, start_date, end_date))

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
