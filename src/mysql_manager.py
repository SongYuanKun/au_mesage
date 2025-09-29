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
                    (trade_date, trade_time, data_type, real_time_price, recycle_price)
                VALUES (%s, %s, %s, %s, %s) \
                """

        values = [
            (item['trade_date'], item['trade_time'], item['data_type'],
             item['real_time_price'], item['recycle_price'])
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
        """获取最新价格数据，每个data_type返回一条"""
        query = """
                SELECT trade_date, trade_time, data_type, real_time_price, recycle_price, created_at
                FROM (
                    SELECT *,
                           ROW_NUMBER() OVER(PARTITION BY data_type ORDER BY created_at DESC) as rn
                    FROM price_data
                ) as sub
                WHERE sub.rn = 1;
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
