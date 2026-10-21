"""数据库操作基类。"""
import logging
from contextlib import contextmanager
from db.pool import ConnectionPool

class BaseDB:
    """提供通用的数据库连接管理和执行逻辑。"""
    
    def __init__(self, pool: ConnectionPool):
        self.pool = pool

    @contextmanager
    def get_cursor(self, dictionary=True):
        """获取数据库游标的上下文管理器。"""
        conn = None
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor(dictionary=dictionary)
            yield cursor
            conn.commit()
        except Exception:
            if conn:
                conn.rollback()
            logging.exception("数据库操作失败")
            raise
        finally:
            if conn:
                conn.close()

    def _exec(self, query, params=None, dictionary=True):
        """执行查询并返回所有结果；数据库异常向上抛出。"""
        with self.get_cursor(dictionary=dictionary) as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()

    def _exec_one(self, query, params=None):
        """执行查询并返回单行结果；数据库异常向上抛出。"""
        with self.get_cursor(dictionary=True) as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()

    def _exec_value(self, query, params=None):
        """执行查询并返回单值；数据库异常向上抛出。"""
        with self.get_cursor(dictionary=False) as cursor:
            cursor.execute(query, params or ())
            row = cursor.fetchone()
            return row[0] if row else None
