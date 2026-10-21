from unittest.mock import MagicMock
from cache import TtlCache
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

def test_portfolio_can_read_only_the_quote_overview_without_credentials(monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.setattr("routes.api.price_routes.api_ttl_cache", TtlCache())
    mock_db = MagicMock()
    mock_db.get_price_overview_data.return_value = []
    mock_db.get_price_overview_data_fallback.return_value = []
    mock_db.get_latest_data_by_type.return_value = []
    client = create_app(mock_db).test_client()

    for origin in ("https://koen.songyuankun.top", "https://unrelated.example"):
        # The fixed allowed origin never reflects an arbitrary requesting origin.
        for _ in range(2):  # Fresh and cached overview responses have the same policy.
            response = client.get("/api/price-overview", headers={"Origin": origin})
            assert response.status_code == 200
            assert response.headers["Access-Control-Allow-Origin"] == "https://koen.songyuankun.top"
            assert "Access-Control-Allow-Credentials" not in response.headers
    mock_db.get_price_overview_data.assert_called_once()
    other = client.get("/api/latest-price", headers={"Origin": "https://koen.songyuankun.top"})
    assert "Access-Control-Allow-Origin" not in other.headers

    monkeypatch.setenv("AUTH_ENABLED", "true")
    assert client.get("/api/price-overview").status_code == 200  # Existing public quote policy.
    blocked = client.get("/api/export/history?data_type=XAU&start_date=2026-05-01&end_date=2026-05-01",
                         headers={"Origin": "https://koen.songyuankun.top"})
    assert blocked.status_code == 401
    assert "Access-Control-Allow-Origin" not in blocked.headers
    assert "Access-Control-Allow-Credentials" not in blocked.headers


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
    mock_db.get_price_history_last_hour.return_value = []
    app = create_app(mock_db)
    client = app.test_client()

    resp = client.get("/api/last-1-hour?data_type=XAU")
    assert resp.status_code == 200
    mock_db.get_price_history_last_hour.assert_called_once_with("XAU")

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
