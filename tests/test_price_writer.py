from unittest.mock import MagicMock
from db.price_writer import PriceWriter


def test_batch_insert_data_ignore():
    mock_pool = MagicMock()
    writer = PriceWriter(mock_pool)
    
    mock_conn = MagicMock()
    mock_pool.get_connection.return_value = mock_conn
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    data = [
        {
            "trade_date": "2026-05-13",
            "trade_time": "10:00:00",
            "data_type": "XAU",
            "real_time_price": 100.0,
            "recycle_price": 99.0,
        }
    ]
    
    writer.batch_insert_data(data)
    
    mock_cursor.executemany.assert_called_once()
    args, kwargs = mock_cursor.executemany.call_args
    assert "INSERT IGNORE INTO price_data" in args[0]
    assert args[1][0] == ("2026-05-13", "10:00:00", "XAU", 100.0, 99.0, 0, 0, "playwright", "CNY")

def test_batch_insert_empty_data():
    mock_pool = MagicMock()
    writer = PriceWriter(mock_pool)
    writer.batch_insert_data([])
    mock_pool.get_connection.assert_not_called()
