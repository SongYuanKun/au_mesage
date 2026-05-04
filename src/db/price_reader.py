"""价格数据读取操作。"""

import logging
from typing import List, Dict, Optional

from db.base import BaseDB


class PriceReader(BaseDB):
    """价格查询：overview / latest / history / daily / time_range"""

    def query_data(self, start_date: str, end_date: str, data_type: Optional[str] = None):
        """查询价格数据"""
        query = ("SELECT trade_date, trade_time, data_type, real_time_price, recycle_price, created_at "
                 "FROM price_data WHERE trade_date BETWEEN %s AND %s ")
        params = [start_date, end_date]
        if data_type:
            query += " AND data_type = %s"
            params.append(data_type)
        query += " ORDER BY trade_date DESC, trade_time DESC"
        return self._exec(query, params)

    def get_latest_data_by_type(self):
        """获取最新价格数据，每个data_type返回一条"""
        return self._exec("""
            SELECT trade_date, trade_time, data_type, real_time_price, recycle_price, created_at
            FROM (
                SELECT *, ROW_NUMBER() OVER(PARTITION BY data_type ORDER BY created_at DESC) as rn
                FROM price_data WHERE trade_date >= CURDATE() - INTERVAL 1 DAY
            ) sub WHERE rn = 1
        """)

    def get_latest_data(self, data_type: Optional[str] = None) -> Optional[Dict]:
        """获取指定data_type的最新一条数据"""
        if not data_type:
            return self.get_latest_data_by_type()
        return self._exec_one(
            ("SELECT trade_date, trade_time, data_type, real_time_price, recycle_price, created_at "
             "FROM price_data WHERE data_type = %s AND recycle_price > 0 "
             "ORDER BY created_at DESC LIMIT 1"), (data_type,))

    def get_price_history(self, data_type: str, limit: int = 20) -> List[Dict]:
        """获取指定data_type的历史价格数据"""
        rows = self._exec(
            ("SELECT trade_date, trade_time, data_type, real_time_price, recycle_price, created_at "
             "FROM price_data WHERE data_type = %s AND recycle_price > 0 "
             "ORDER BY created_at DESC LIMIT %s"), (data_type, limit))
        return list(reversed(rows))

    def get_latest_market_price(self, data_type: str) -> Optional[float]:
        """
        最新「可比价」：与页面主推的回收口径一致；优先大盘实时价，
        缺失或为 0 时回退 recycle_price，避免仅有回收价时 SSE/历史对比失败。
        """
        return self._exec_value(
            (
                "SELECT COALESCE(NULLIF(real_time_price, 0), recycle_price) "
                "FROM price_data WHERE data_type = %s AND recycle_price > 0 "
                "ORDER BY created_at DESC LIMIT 1"
            ),
            (data_type,),
        )

    def get_daily_history(self, date: str, data_type: Optional[str] = None) -> List[Dict]:
        """获取指定日期的历史数据"""
        query = ("SELECT trade_date, trade_time, data_type, real_time_price, recycle_price, created_at "
                 "FROM price_data WHERE trade_date = %s AND recycle_price > 0 ")
        params = [date]
        if data_type:
            query += " AND data_type = %s"
            params.append(data_type)
        query += " ORDER BY created_at ASC"
        return self._exec(query, params)

    def get_price_overview_data(self, today_str: str, yesterday_str: str) -> List[Dict]:
        """单条SQL获取价格概览：当前价、昨日收盘、今日高低"""
        return self._exec("""
            SELECT cur.data_type, cur.recycle_price, cur.real_time_price, cur.created_at AS updated_at,
                   yest.recycle_price AS yesterday_close, hl.today_high, hl.today_low
            FROM (
                SELECT data_type, recycle_price, real_time_price, created_at,
                       ROW_NUMBER() OVER(PARTITION BY data_type ORDER BY created_at DESC) AS rn
                FROM price_data WHERE recycle_price > 0 AND trade_date >= %s
            ) cur
            LEFT JOIN (
                SELECT data_type, recycle_price,
                       ROW_NUMBER() OVER(PARTITION BY data_type ORDER BY created_at DESC) AS rn
                FROM price_data WHERE recycle_price > 0 AND trade_date = %s
            ) yest ON cur.data_type = yest.data_type AND yest.rn = 1
            LEFT JOIN (
                SELECT data_type, MAX(recycle_price) AS today_high, MIN(recycle_price) AS today_low
                FROM price_data WHERE recycle_price > 0 AND trade_date = %s GROUP BY data_type
            ) hl ON cur.data_type = hl.data_type
            WHERE cur.rn = 1
        """, (yesterday_str, yesterday_str, today_str))

    def get_price_history_by_time_range(self, data_type: str, start_time: str, end_time: str) -> List[Dict]:
        """获取指定时间范围内的价格数据"""
        return self._exec(
            ("SELECT trade_date, trade_time, data_type, real_time_price, recycle_price, created_at "
             "FROM price_data WHERE data_type = %s AND recycle_price > 0 "
             "AND created_at >= %s AND created_at <= %s ORDER BY created_at ASC"),
            (data_type, start_time, end_time))
