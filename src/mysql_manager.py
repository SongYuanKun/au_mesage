import logging
from typing import List, Dict, Optional

from mysql.connector import Error, pooling


class MySQLManager:
    def __init__(self, config: Dict):
        self.config = config
        self.connection_pool = None
        self._initialize_pool()

    def _initialize_pool(self):
        """初始化数据库连接池"""
        try:
            self.connection_pool = pooling.MySQLConnectionPool(
                pool_name="price_pool",
                pool_size=5,
                **self.config
            )
            logging.info("数据库连接池初始化成功")
        except Error as e:
            logging.error(f"连接池初始化失败: {e}")
            raise

    def batch_insert_data(self, data_list: List[Dict]):
        """批量插入价格数据"""
        if not data_list:
            return

        query = """
                INSERT INTO price_data
                    (trade_date, trade_time, data_type, real_time_price, recycle_price, high_price, low_price)
                VALUES (%s, %s, %s, %s, %s, %s, %s) \
                """

        values = [
            (item['trade_date'], item['trade_time'], item['data_type'],
             item['real_time_price'], item['recycle_price'],
             item.get('high_price', 0), item.get('low_price', 0))
            for item in data_list
        ]

        connection = None
        try:
            connection = self.connection_pool.get_connection()
            cursor = connection.cursor()
            cursor.executemany(query, values)
            connection.commit()
            logging.info(f"成功插入 {len(data_list)} 条数据")
        except Error as e:
            logging.error(f"批量插入失败: {e}")
            if connection:
                connection.rollback()
        finally:
            if connection:
                connection.close()

    def query_data(self, start_date: str, end_date: str, data_type: Optional[str] = None):
        """查询价格数据"""
        query = """
                SELECT trade_date, trade_time, data_type, real_time_price, recycle_price, created_at
                FROM price_data
                WHERE trade_date BETWEEN %s AND %s \
                """
        params = [start_date, end_date]

        if data_type:
            query += " AND data_type = %s"
            params.append(data_type)

        query += " ORDER BY trade_date DESC, trade_time DESC"

        connection = None
        try:
            connection = self.connection_pool.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params)
            results = cursor.fetchall()
            return results
        except Error as e:
            logging.error(f"数据查询失败: {e}")
            return []
        finally:
            if connection:
                connection.close()

    def get_latest_data_by_type(self):
        """获取最新价格数据，每个data_type返回一条（限制最近2天避免全表扫描）"""
        query = """
                SELECT trade_date, trade_time, data_type, real_time_price, recycle_price, created_at
                FROM (
                    SELECT trade_date, trade_time, data_type, real_time_price, recycle_price, created_at,
                           ROW_NUMBER() OVER(PARTITION BY data_type ORDER BY created_at DESC) as rn
                    FROM price_data
                    WHERE trade_date >= CURDATE() - INTERVAL 1 DAY
                ) as sub
                WHERE sub.rn = 1
        """

        connection = None
        try:
            connection = self.connection_pool.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query)
            results = cursor.fetchall()
            return results
        except Error as e:
            logging.error(f"获取最新数据失败: {e}")
            return []
        finally:
            if connection:
                connection.close()

    def get_latest_data(self, data_type: Optional[str] = None) -> Optional[Dict]:
        """
        获取指定data_type的最新一条数据。
        如果data_type为None，则返回所有data_type的最新数据（每个data_type一条）。
        """
        if data_type:
            query = """
                    SELECT trade_date, trade_time, data_type, real_time_price, recycle_price, created_at
                    FROM price_data
                    WHERE data_type = %s
                        and recycle_price >0
                    ORDER BY created_at DESC
                    LIMIT 1
            """
            params = (data_type,)
        else:
            # If no specific data_type is requested, return the latest for each type
            return self.get_latest_data_by_type()

        connection = None
        try:
            connection = self.connection_pool.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result
        except Error as e:
            logging.error(f"获取最新数据失败 (type={data_type}): {e}")
            return None
        finally:
            if connection:
                connection.close()

    def get_price_history(self, data_type: str, limit: int = 20) -> List[Dict]:
        """
        获取指定data_type的历史价格数据。
        """
        query = """
                SELECT trade_date, trade_time, data_type, real_time_price, recycle_price, created_at
                FROM price_data
                WHERE data_type = %s
                  and recycle_price > 0
                ORDER BY created_at DESC
                LIMIT %s \
                """
        params = (data_type, limit)

        connection = None
        try:
            connection = self.connection_pool.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params)
            results = cursor.fetchall()
            # ECharts expects data in chronological order for line charts
            return list(reversed(results))
        except Error as e:
            logging.error(f"获取历史数据失败 (type={data_type}): {e}")
            return []
        finally:
            if connection:
                connection.close()

    def get_latest_market_price(self, data_type: str) -> Optional[float]:
        """
        获取指定data_type的最新市场价格 (real_time_price)。
        """
        query = """
                SELECT real_time_price
                FROM price_data
                WHERE data_type = %s
                  and recycle_price > 0
                ORDER BY created_at DESC
                LIMIT 1 \
                """
        params = (data_type,)

        connection = None
        try:
            connection = self.connection_pool.get_connection()
            cursor = connection.cursor() # Use default cursor for single value
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else None
        except Error as e:
            logging.error(f"获取最新市场价格失败 (type={data_type}): {e}")
            return None
        finally:
            if connection:
                connection.close()

    def get_daily_history(self, date: str, data_type: Optional[str] = None) -> List[Dict]:
        """
        获取指定日期和data_type的所有历史数据。
        """
        query = """
                SELECT trade_date, trade_time, data_type, real_time_price, recycle_price, created_at
                FROM price_data
                WHERE trade_date = %s
                  and recycle_price > 0 \
                """
        params = [date]

        if data_type:
            query += " AND data_type = %s"
            params.append(data_type)

        query += " ORDER BY created_at ASC" # Order chronologically for display

        connection = None
        try:
            connection = self.connection_pool.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params)
            results = cursor.fetchall()
            return results
        except Error as e:
            logging.error(f"获取每日历史数据失败 (date={date}, type={data_type}): {e}")
            return []
        finally:
            if connection:
                connection.close()

    def get_price_overview_data(self, today_str: str, yesterday_str: str) -> List[Dict]:
        """
        单条 SQL 获取价格概览：当前价、昨日收盘、今日高低。
        仅扫描最近两天数据，避免全表扫描。
        """
        query = """
                SELECT
                    cur.data_type,
                    cur.recycle_price,
                    cur.real_time_price,
                    cur.created_at   AS updated_at,
                    yest.recycle_price AS yesterday_close,
                    hl.today_high,
                    hl.today_low
                FROM (
                    SELECT data_type, recycle_price, real_time_price, created_at,
                           ROW_NUMBER() OVER(PARTITION BY data_type ORDER BY created_at DESC) AS rn
                    FROM price_data
                    WHERE recycle_price > 0 AND trade_date >= %s
                ) cur
                LEFT JOIN (
                    SELECT data_type, recycle_price,
                           ROW_NUMBER() OVER(PARTITION BY data_type ORDER BY created_at DESC) AS rn
                    FROM price_data
                    WHERE recycle_price > 0 AND trade_date = %s
                ) yest ON cur.data_type = yest.data_type AND yest.rn = 1
                LEFT JOIN (
                    SELECT data_type,
                           MAX(recycle_price) AS today_high,
                           MIN(recycle_price) AS today_low
                    FROM price_data
                    WHERE recycle_price > 0 AND trade_date = %s
                    GROUP BY data_type
                ) hl ON cur.data_type = hl.data_type
                WHERE cur.rn = 1
        """
        params = (yesterday_str, yesterday_str, today_str)
        connection = None
        try:
            connection = self.connection_pool.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params)
            return cursor.fetchall()
        except Error as e:
            logging.error(f"获取价格概览数据失败: {e}")
            return []
        finally:
            if connection:
                connection.close()

    def get_last_n_days_daily_price(self, data_type: str, start_date: str, end_date: str) -> List[Dict]:
        """
        单条 SQL 获取日期范围内每天最后一条回收价格（窗口函数）。
        返回 [{'date': '2026-03-14', 'recycle_price': 688.12}, ...]
        """
        query = """
                SELECT trade_date AS date, recycle_price
                FROM (
                    SELECT trade_date, recycle_price,
                           ROW_NUMBER() OVER(PARTITION BY trade_date ORDER BY created_at DESC) AS rn
                    FROM price_data
                    WHERE data_type = %s
                      AND recycle_price > 0
                      AND trade_date >= %s
                      AND trade_date <= %s
                ) sub
                WHERE sub.rn = 1
                ORDER BY date ASC
        """
        params = (data_type, start_date, end_date)
        connection = None
        try:
            connection = self.connection_pool.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params)
            return cursor.fetchall()
        except Error as e:
            logging.error(f"获取近N天每日价格失败 (type={data_type}): {e}")
            return []
        finally:
            if connection:
                connection.close()

    def get_ohlc_trend(self, data_type: str, start_date: str, end_date: str) -> List[Dict]:
        """
        获取日K线数据（开盘/最高/最低/收盘），用于K线图。
        使用 GROUP_CONCAT 技巧获取每天的首尾价格。
        """
        query = """
                SELECT
                    trade_date AS date,
                    CAST(SUBSTRING_INDEX(GROUP_CONCAT(recycle_price ORDER BY created_at ASC), ',', 1) AS DECIMAL(10,4)) AS open_price,
                    MAX(recycle_price) AS high_price,
                    MIN(recycle_price) AS low_price,
                    CAST(SUBSTRING_INDEX(GROUP_CONCAT(recycle_price ORDER BY created_at DESC), ',', 1) AS DECIMAL(10,4)) AS close_price
                FROM price_data
                WHERE data_type = %s
                  AND recycle_price > 0
                  AND trade_date BETWEEN %s AND %s
                GROUP BY trade_date
                ORDER BY trade_date ASC
        """
        params = (data_type, start_date, end_date)
        connection = None
        try:
            connection = self.connection_pool.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params)
            return cursor.fetchall()
        except Error as e:
            logging.error(f"获取OHLC趋势数据失败 (type={data_type}): {e}")
            return []
        finally:
            if connection:
                connection.close()

    def get_intraday_trend(self, data_type: str, date_str: str) -> List[Dict]:
        """获取指定日期的分钟级别走势数据（用于日内图表）"""
        query = """
                SELECT trade_time AS time, recycle_price, real_time_price, created_at
                FROM price_data
                WHERE data_type = %s
                  AND recycle_price > 0
                  AND trade_date = %s
                ORDER BY created_at ASC
        """
        params = (data_type, date_str)
        connection = None
        try:
            connection = self.connection_pool.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params)
            return cursor.fetchall()
        except Error as e:
            logging.error(f"获取日内趋势数据失败 (type={data_type}, date={date_str}): {e}")
            return []
        finally:
            if connection:
                connection.close()

    def get_gold_silver_ratio(self, start_date: str, end_date: str) -> List[Dict]:
        """
        获取金银比走势数据。
        每天取最后一条回收价格，计算 gold_close / silver_close。
        """
        query = """
                SELECT g.date, g.close_price AS gold_close, s.close_price AS silver_close,
                       ROUND(g.close_price / s.close_price, 2) AS ratio
                FROM (
                    SELECT trade_date AS date,
                           CAST(SUBSTRING_INDEX(GROUP_CONCAT(recycle_price ORDER BY created_at DESC), ',', 1) AS DECIMAL(10,4)) AS close_price
                    FROM price_data
                    WHERE data_type = '黄 金' AND recycle_price > 0
                      AND trade_date BETWEEN %s AND %s
                    GROUP BY trade_date
                ) g
                JOIN (
                    SELECT trade_date AS date,
                           CAST(SUBSTRING_INDEX(GROUP_CONCAT(recycle_price ORDER BY created_at DESC), ',', 1) AS DECIMAL(10,4)) AS close_price
                    FROM price_data
                    WHERE data_type = '白 银' AND recycle_price > 0
                      AND trade_date BETWEEN %s AND %s
                    GROUP BY trade_date
                ) s ON g.date = s.date
                ORDER BY g.date ASC
        """
        params = (start_date, end_date, start_date, end_date)
        connection = None
        try:
            connection = self.connection_pool.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params)
            return cursor.fetchall()
        except Error as e:
            logging.error(f"获取金银比数据失败: {e}")
            return []
        finally:
            if connection:
                connection.close()

    def get_price_history_by_time_range(self, data_type: str, start_time: str, end_time: str) -> List[Dict]:
        """
        获取指定时间范围内的价格数据。
        start_time, end_time 格式: 'YYYY-MM-DD HH:MM:SS'
        """
        query = """
                SELECT trade_date, trade_time, data_type, real_time_price, recycle_price, created_at
                FROM price_data
                WHERE data_type = %s
                  AND recycle_price > 0
                  AND created_at >= %s
                  AND created_at <= %s
                ORDER BY created_at ASC
        """
        params = (data_type, start_time, end_time)

        connection = None
        try:
            connection = self.connection_pool.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params)
            results = cursor.fetchall()
            return results
        except Error as e:
            logging.error(f"获取时间范围内数据失败 (type={data_type}, start={start_time}, end={end_time}): {e}")
            return []
        finally:
            if connection:
                connection.close()
