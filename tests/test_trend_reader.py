import sqlite3
from unittest.mock import MagicMock

from db.trend_reader import TrendReader


def test_gold_silver_ratio_executes_and_never_crosses_source_or_currency():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE price_data (
          trade_date TEXT, data_type TEXT, source TEXT, currency TEXT,
          recycle_price REAL, created_at TEXT
        )
        """
    )
    conn.executemany(
        "INSERT INTO price_data VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("2026-10-20", "XAU", "gold_api", "USD", 2000, "2026-10-20 10:00:00"),
            ("2026-10-20", "XAG", "other_api", "USD", 25, "2026-10-20 10:00:00"),
            ("2026-10-20", "黄 金", "playwright", "CNY", 500, "2026-10-20 10:00:00"),
            ("2026-10-20", "白 银", "playwright", "CNY", 5, "2026-10-20 10:00:00"),
            ("2026-10-20", "白 银", "playwright", "USD", 25, "2026-10-20 10:00:00"),
        ],
    )
    reader = TrendReader(MagicMock())

    def execute(query, params):
        rows = conn.execute(query.replace("%s", "?"), params).fetchall()
        return [dict(row) for row in rows]

    reader._exec = execute
    rows = reader.get_gold_silver_ratio("2026-10-20", "2026-10-20")

    assert rows == [
        {"date": "2026-10-20", "gold_close": 500.0, "silver_close": 5.0, "ratio": 100.0}
    ]
