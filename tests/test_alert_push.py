from unittest.mock import MagicMock
from route import create_app

def test_price_alert_push_success(monkeypatch):
    mock_db = MagicMock()
    mock_db.get_latest_market_price.return_value = 100.0
    app = create_app(mock_db)
    client = app.test_client()
    
    mock_wechat = MagicMock(return_value=True)
    monkeypatch.setattr("webhook_notifier.send_wechat", mock_wechat)
    
    resp = client.post("/api/price-alert/push", json={
        "data_type": "XAU",
        "target": 90,
        "op": "gte",
        "channels": ["wechat"]
    })
    
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["triggered"] is True
    assert "wechat" in data["sent_channels"]
    mock_wechat.assert_called_once()

def test_price_alert_push_not_triggered():
    mock_db = MagicMock()
    mock_db.get_latest_market_price.return_value = 80.0
    app = create_app(mock_db)
    client = app.test_client()
    
    resp = client.post("/api/price-alert/push", json={
        "data_type": "XAU",
        "target": 90,
        "op": "gte",
        "channels": ["wechat"]
    })
    
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["triggered"] is False
    assert len(data["sent_channels"]) == 0

def test_price_alert_push_missing_args():
    app = create_app(MagicMock())
    client = app.test_client()
    resp = client.post("/api/price-alert/push", json={})
    assert resp.status_code == 400
    
    resp2 = client.post("/api/price-alert/push", json={"data_type": "XAU", "target": "invalid"})
    assert resp2.status_code == 400
