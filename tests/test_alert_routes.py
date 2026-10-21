from unittest.mock import MagicMock
from route import create_app
from routes.api.cache import api_ttl_cache

def test_price_alert_subscribe_caching(monkeypatch):
    api_ttl_cache.clear()
    
    mock_db = MagicMock()
    # Mock return 100 on first call, but the cache should prevent second call
    mock_db.get_latest_market_price.return_value = 100.0
    
    app = create_app(mock_db)
    client = app.test_client()
    
    # We need to test the SSE stream, which is an infinite loop
    # Let's mock time.sleep to raise an Exception so the loop breaks
    def fake_sleep(*args, **kwargs):
        raise StopIteration("Break loop")
        
    monkeypatch.setattr("routes.api.alert_routes.time.sleep", fake_sleep)
    
    # We call it twice to ensure cache is hit
    try:
        resp1 = client.get("/api/price-alert/subscribe?data_type=XAU&target=90&op=gte")
        list(resp1.iter_encoded())
    except StopIteration:
        pass
        
    assert mock_db.get_latest_market_price.call_count == 1
    
    try:
        resp2 = client.get("/api/price-alert/subscribe?data_type=XAU&target=90&op=gte")
        list(resp2.iter_encoded())
    except StopIteration:
        pass
        
    # Call count should STILL be 1 because it's cached!
    assert mock_db.get_latest_market_price.call_count == 1

def test_price_alert_subscribe_missing_params():
    app = create_app(MagicMock())
    client = app.test_client()
    resp = client.get("/api/price-alert/subscribe")
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "INVALID_ARGUMENT"


def test_price_alert_subscribe_sends_error_event_when_db_fails():
    api_ttl_cache.clear()
    mock_db = MagicMock()
    mock_db.get_latest_market_price.side_effect = RuntimeError("db unavailable")
    client = create_app(mock_db).test_client()

    resp = client.get("/api/price-alert/subscribe?data_type=XAU&target=90&op=gte")
    body = b"".join(resp.iter_encoded()).decode()

    assert resp.status_code == 200
    assert "event: error" in body


def test_alert_endpoints_require_user_token_when_auth_is_enabled(monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_USER_TOKEN", "user-token")
    api_ttl_cache.clear()
    mock_db = MagicMock()
    mock_db.get_latest_market_price.return_value = 100.0
    client = create_app(mock_db).test_client()
    assert client.get("/api/alert-channels").status_code == 401
    assert client.post("/api/price-alert/push", json={"data_type": "XAU", "target": 90}).status_code == 401
    assert client.get("/api/alert-channels", headers={"Authorization": "Bearer user-token"}).status_code == 200


def test_sse_cookie_cannot_authorize_push(monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_USER_TOKEN", "user-token")
    api_ttl_cache.clear()
    mock_db = MagicMock()
    mock_db.get_latest_market_price.return_value = 100.0
    client = create_app(mock_db).test_client()

    session = client.post("/api/auth/session", headers={"Authorization": "Bearer user-token"})
    assert session.status_code == 200
    assert "HttpOnly" in session.headers["Set-Cookie"]
    assert client.get("/api/alert-channels").status_code == 200
    assert client.post("/api/price-alert/push", json={"data_type": "XAU", "target": 90}).status_code == 401


def test_alert_push_is_rate_limited():
    api_ttl_cache.clear()
    mock_db = MagicMock()
    mock_db.get_latest_market_price.return_value = 100.0
    client = create_app(mock_db).test_client()
    payload = {"data_type": "XAU", "target": 90, "channels": []}
    for _ in range(10):
        assert client.post("/api/price-alert/push", json=payload).status_code == 200
    response = client.post("/api/price-alert/push", json=payload)
    assert response.status_code == 429
    assert response.get_json()["error"]["code"] == "RATE_LIMITED"
