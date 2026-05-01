"""汇率数据读取操作。"""

import logging
from typing import Optional

from db.base import BaseDB


class ExchangeReader(BaseDB):
    """汇率查询：get_latest_exchange_rate"""

    def get_latest_exchange_rate(self, base: str, target: str) -> Optional[float]:
        """获取最新汇率"""
        return self._exec_value(
            "SELECT rate FROM exchange_rate "
            "WHERE base_currency = %s AND target_currency = %s "
            "ORDER BY created_at DESC LIMIT 1",
            (base, target))
