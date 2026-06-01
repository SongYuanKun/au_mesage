from unittest.mock import MagicMock
from route import create_app

def test_price_overview():
    mock_db = MagicMock()
    mock_db.get_price_overview_data.return_value = [
        {"data_type": "XAU", "recycle_price": 100.0}
    ]
    app = create_app(mock_db)
    client = app.test_client()
    resp = client.get("/api/price-overview")
    assert resp.status_code == 200

def test_latest_price():
    mock_db = MagicMock()
    mock_db.get_latest_data.return_value = {"recycle_price": 100.0}
    mock_db.get_latest_data_by_type.return_value = [{"recycle_price": 100.0}]
    
    app = create_app(mock_db)
    client = app.test_client()
    
    resp = client.get("/api/latest-price")
    assert resp.status_code == 200
    
    resp2 = client.get("/api/latest-price?data_type=XAU")
    assert resp2.status_code == 200

def test_last_1_hour():
    mock_db = MagicMock()
    mock_db.get_price_history_by_time_range.return_value = []
    app = create_app(mock_db)
    client = app.test_client()

    resp = client.get("/api/last-1-hour?data_type=XAU")
    assert resp.status_code == 200
    mock_db.get_price_history_by_time_range.assert_called_once()
    start, end = mock_db.get_price_history_by_time_range.call_args[0][1:]
    assert start[:10] == end[:10]
    assert start[11:13] <= end[11:13]

def test_last_7_days():
    mock_db = MagicMock()
    mock_db.get_last_n_days_daily_price.return_value = []
    app = create_app(mock_db)
    client = app.test_client()
    
    resp = client.get("/api/last-7-days?data_type=XAU")
    assert resp.status_code == 200

def test_price_trend():
    mock_db = MagicMock()
    mock_db.get_intraday_trend.return_value = []
    mock_db.get_ohlc_trend.return_value = []
    app = create_app(mock_db)
    client = app.test_client()
    
    resp = client.get("/api/price-trend?data_type=XAU&range=1d")
    assert resp.status_code == 200
    
    resp2 = client.get("/api/price-trend?data_type=XAU&range=7d")
    assert resp2.status_code == 200

def test_gold_silver_ratio():
    mock_db = MagicMock()
    mock_db.get_gold_silver_ratio.return_value = []
    app = create_app(mock_db)
    client = app.test_client()
    
    resp = client.get("/api/gold-silver-ratio?range=30d")
    assert resp.status_code == 200
