from unittest.mock import MagicMock

from route import create_app


def test_export_history_csv():
    mm = MagicMock()
    mm.query_data.return_value = [
        {
            "trade_date": "2026-05-01",
            "trade_time": "12:00:00",
            "data_type": "XAU",
            "real_time_price": 1,
            "recycle_price": 2,
            "source": "gold_api",
            "currency": "CNY",
            "created_at": "2026-05-01 12:00:00",
        }
    ]
    app = create_app(mm)
    client = app.test_client()
    resp = client.get(
        "/api/export/history?data_type=XAU&start_date=2026-05-01&end_date=2026-05-01&format=csv&limit=10"
    )
    assert resp.status_code == 200
    assert resp.mimetype == "text/csv"
    body = resp.get_data(as_text=True)
    assert "trade_date" in body
    assert "XAU" in body


def test_export_history_missing_param_returns_api_error():
    app = create_app(MagicMock())
    client = app.test_client()
    resp = client.get("/api/export/history")
    assert resp.status_code == 400
    j = resp.get_json()
    assert j["success"] is False
    assert j["error"]["code"] == "INVALID_ARGUMENT"

