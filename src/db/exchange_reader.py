"""汇率数据读取操作。"""

import logging
from typing import Optional

from mysql.connector import Error

from db.pool import ConnectionPool


class ExchangeReader:
    """汇率查询：get_latest_exchange_rate"""

    def __init__(self, pool: ConnectionPool):
        self.pool = pool

    def get_latest_exchange_rate(self, base: str, target: str) -> Optional[float]:
        """获取最新汇率"""
        conn = None
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT rate FROM exchange_rate "
                "WHERE base_currency = %s AND target_currency = %s "
                "ORDER BY created_at DESC LIMIT 1",
                (base, target))
            row = cursor.fetchone()
            return float(row[0]) if row else None
        except Error as e:
            logging.error(f"获取汇率失败 ({base}/{target}): {e}")
            return None
        finally:
            if conn:
                conn.close()
