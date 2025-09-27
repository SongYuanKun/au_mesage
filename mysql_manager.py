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
                SELECT trade_date, trade_time, data_type, real_time_price, recycle_price
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
            logging.error("数据查询失败: {e}")
            return []
        finally:
            if connection:
                connection.close()

    def get_latest_data(self, data_type: Optional[str] = None):
        """获取最新价格数据"""
        query = """
                SELECT trade_date, trade_time, data_type, real_time_price, recycle_price, created_at
                FROM price_data \
                """
        params = []

        if data_type:
            query += " WHERE data_type = %s"
            params.append(data_type)

        query += " ORDER BY created_at DESC LIMIT 1"

        connection = None
        try:
            connection = self.connection_pool.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result
        except Error as e:
            logging.error(f"获取最新数据失败: {e}")
            return None
        finally:
            if connection:
                connection.close()