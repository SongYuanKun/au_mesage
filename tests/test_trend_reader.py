import sqlite3
from unittest.mock import MagicMock

from db.trend_reader import TrendReader


def test_ohlc_uses_all_prices_in_each_day_and_preserves_open_and_close():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE price_data (
          trade_date TEXT, data_type TEXT, recycle_price REAL, created_at TEXT
        )
        """
    )
    conn.executemany(
        "INSERT INTO price_data VALUES (?, ?, ?, ?)",
        [
            ("2026-11-04", "XAU", 1, "2026-11-04 09:00:00"),
            ("2026-11-05", "XAU", 100, "2026-11-05 09:00:00"),
            ("2026-11-05", "XAU", 120, "2026-11-05 10:00:00"),
            ("2026-11-05", "XAU", 80, "2026-11-05 11:00:00"),
            ("2026-11-05", "XAU", 110, "2026-11-05 12:00:00"),
            ("2026-11-05", "XAG", 1000, "2026-11-05 13:00:00"),
            ("2026-11-05", "XAU", 0, "2026-11-05 14:00:00"),
            ("2026-11-06", "XAU", 200, "2026-11-06 09:00:00"),
            ("2026-11-06", "XAU", 190, "2026-11-06 10:00:00"),
        ],
    )
    reader = TrendReader(MagicMock())

    def execute(query, params):
        rows = conn.execute(query.replace("%s", "?"), params).fetchall()
        return [dict(row) for row in rows]

    reader._exec = execute

    assert reader.get_ohlc_trend("XAU", "2026-11-05", "2026-11-06") == [
        {"date": "2026-11-05", "open_price": 100.0, "high_price": 120.0,
         "low_price": 80.0, "close_price": 110.0},
        {"date": "2026-11-06", "open_price": 200.0, "high_price": 200.0,
         "low_price": 190.0, "close_price": 190.0},
    ]


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
