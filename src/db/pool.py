"""数据库连接池管理。"""

import logging
from typing import Dict

from mysql.connector import Error, pooling


class ConnectionPool:
    """MySQL 连接池单例管理。"""

    def __init__(self, config: Dict):
        self.config = config
        self.pool: pooling.MySQLConnectionPool = None
        self._initialize()

    def _initialize(self):
        """初始化连接池。"""
        try:
            self.pool = pooling.MySQLConnectionPool(
                pool_name="price_pool",
                pool_size=5,
                **self.config
            )
            logging.info("数据库连接池初始化成功")
        except Error as e:
            logging.error(f"连接池初始化失败: {e}")
            raise

    def get_connection(self):
        """从池中获取一个连接。"""
        return self.pool.get_connection()
