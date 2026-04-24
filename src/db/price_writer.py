"""价格数据写入操作。"""

import logging
from typing import List, Dict

from mysql.connector import Error

from db.pool import ConnectionPool


class PriceWriter:
    """采集器写入：price_data / exchange_rate / daily_ohlc"""

    def __init__(self, pool: ConnectionPool):
        self.pool = pool

    def batch_insert_data(self, data_list: List[Dict]):
        """批量插入价格数据"""
        if not data_list:
            return

        query = """
                INSERT INTO price_data
                    (trade_date, trade_time, data_type, real_time_price, recycle_price,
                     high_price, low_price, source, currency)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) \
                """

        values = [
            (item['trade_date'], item['trade_time'], item['data_type'],
             item['real_time_price'], item['recycle_price'],
             item.get('high_price', 0), item.get('low_price', 0),
             item.get('source', 'playwright'), item.get('currency', 'CNY'))
            for item in data_list
        ]

        connection = None
        try:
            connection = self.pool.get_connection()
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

    def upsert_exchange_rate(self, base: str, target: str, rate: float, source: str):
        """插入或更新汇率记录"""
        query = """
                INSERT INTO exchange_rate (base_currency, target_currency, rate, source)
                VALUES (%s, %s, %s, %s)
        """
        connection = None
        try:
            connection = self.pool.get_connection()
            cursor = connection.cursor()
            cursor.execute(query, (base, target, rate, source))
            connection.commit()
        except Error as e:
            logging.error(f"写入汇率失败: {e}")
            if connection:
                connection.rollback()
        finally:
            if connection:
                connection.close()

    def upsert_daily_ohlc(self, trade_date: str, data_type: str, source: str,
                          currency: str, open_price: float, high_price: float,
                          low_price: float, close_price: float, volume: float = None):
        """插入或更新日线OHLC（同一 date+type+source 只保留最新）"""
        query = """
                INSERT INTO daily_ohlc
                    (trade_date, data_type, source, currency,
                     open_price, high_price, low_price, close_price, volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    open_price = VALUES(open_price),
                    high_price = VALUES(high_price),
                    low_price  = VALUES(low_price),
                    close_price = VALUES(close_price),
                    volume = VALUES(volume),
                    created_at = CURRENT_TIMESTAMP
        """
        connection = None
        try:
            connection = self.pool.get_connection()
            cursor = connection.cursor()
            cursor.execute(query, (trade_date, data_type, source, currency,
                                   open_price, high_price, low_price, close_price, volume))
            connection.commit()
        except Error as e:
            logging.error(f"写入日线OHLC失败 ({data_type},{trade_date}): {e}")
            if connection:
                connection.rollback()
        finally:
            if connection:
                connection.close()
