from unittest.mock import MagicMock

import pytest

from db.price_writer import PriceWriter

def test_upsert_exchange_rate():
    mock_pool = MagicMock()
    writer = PriceWriter(mock_pool)
    mock_conn = MagicMock()
    mock_pool.get_connection.return_value = mock_conn
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    writer.upsert_exchange_rate("USD", "CNY", 7.0, "test")
    mock_cursor.execute.assert_called_once()

def test_upsert_daily_ohlc():
    mock_pool = MagicMock()
    writer = PriceWriter(mock_pool)
    mock_conn = MagicMock()
    mock_pool.get_connection.return_value = mock_conn
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    writer.upsert_daily_ohlc("2026-05-13", "XAU", "gold_api", "CNY", 100, 110, 90, 105, 1000)
    mock_cursor.execute.assert_called_once()


def test_upsert_exchange_rate_failure_propagates():
    mock_pool = MagicMock()
    writer = PriceWriter(mock_pool)
    cursor = mock_pool.get_connection.return_value.cursor.return_value
    cursor.execute.side_effect = RuntimeError("exchange write failed")

    with pytest.raises(RuntimeError, match="exchange write failed"):
        writer.upsert_exchange_rate("USD", "CNY", 7.0, "test")


def test_upsert_daily_ohlc_failure_propagates():
    mock_pool = MagicMock()
    writer = PriceWriter(mock_pool)
    cursor = mock_pool.get_connection.return_value.cursor.return_value
    cursor.execute.side_effect = RuntimeError("ohlc write failed")

    with pytest.raises(RuntimeError, match="ohlc write failed"):
        writer.upsert_daily_ohlc(
            "2026-05-13",
            "XAU",
            "gold_api",
            "CNY",
            100,
            110,
            90,
            105,
            1000,
        )
