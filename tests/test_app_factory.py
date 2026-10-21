"""应用工厂与路由注册冒烟测试（无需真实 MySQL）。"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.parse import quote

from route import create_app
from routes.api.cache import api_ttl_cache


_OVERVIEW_ROW = {
    "data_type": "XAU",
    "recycle_price": 100.0,
    "real_time_price": 101.0,
    "yesterday_close": 99.0,
    "today_high": 102.0,
    "today_low": 98.0,
    "updated_at": "2025-01-01 12:00:00",
}


def test_create_app_registers_health():
    mock_db = MagicMock()
    mock_db.get_latest_updates_by_group.return_value = [{"latest_at": datetime.now().isoformat()}]
    app = create_app(mock_db)
    client = app.test_client()
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "healthy"
    assert body["service"] == "price-data-api"


def test_health_returns_503_when_database_readiness_probe_fails():
    mock_db = MagicMock()
    mock_db.get_latest_updates_by_group.side_effect = RuntimeError("database down")
    resp = create_app(mock_db).test_client().get("/api/health")
    assert resp.status_code == 503
    assert resp.get_json()["reason"] == "database_unavailable"


def test_pages_routes_registered():
    app = create_app(MagicMock())
    client = app.test_client()
    # 无数据库时首页模板仍可渲染（不触发 DB 的查询在后续请求）
    r = client.get("/")
    assert r.status_code == 200


def test_react_spa_uses_explicit_prefix_and_does_not_swallow_api_404(tmp_path):
    app = create_app(MagicMock())
    spa_dir = Path(tmp_path) / "spa"
    spa_dir.mkdir()
    (spa_dir / "index.html").write_text("<div id='root'>spa</div>", encoding="utf-8")
    (spa_dir / "assets").mkdir()
    (spa_dir / "assets" / "app.js").write_text("console.log('spa')", encoding="utf-8")
    app.static_folder = str(tmp_path)
    client = app.test_client()

    for path in ("/app", "/app/"):
        response = client.get(path)
        assert response.status_code == 200
        assert "Location" not in response.headers
        assert response.data == b"<div id='root'>spa</div>"
    assert client.get("/app/analysis").data == b"<div id='root'>spa</div>"
    assert client.get("/app/assets/app.js").data == b"console.log('spa')"
    assert client.get("/app/assets/missing.js").status_code == 404
    api_404 = client.get("/api/not-a-route")
    assert api_404.status_code == 404
    assert api_404.get_json()["error"]["code"] == "NOT_FOUND"


def test_react_runtime_config_tracks_backend_auth_setting(monkeypatch):
    """The SPA bootstrap must use Flask's runtime AUTH_ENABLED value."""
    app = create_app(MagicMock())
    client = app.test_client()

    monkeypatch.setenv("AUTH_ENABLED", "true")
    enabled = client.get("/app/runtime-config.js")
    assert enabled.status_code == 200
    assert enabled.get_data(as_text=True) == 'window.__AU_RUNTIME_CONFIG__ = {"authEnabled": true};\n'
    assert enabled.headers["Cache-Control"] == "no-store"

    monkeypatch.setenv("AUTH_ENABLED", "false")
    disabled = client.get("/app/runtime-config.js")
    assert disabled.get_data(as_text=True) == 'window.__AU_RUNTIME_CONFIG__ = {"authEnabled": false};\n'

    vite_entry = Path(__file__).resolve().parents[1] / "index.html"
    assert '<script src="/app/runtime-config.js"></script>' in vite_entry.read_text(encoding="utf-8")


def test_api_calculate_with_mock_market_data():
    mm = MagicMock()
    mm.get_latest_data.return_value = {"recycle_price": 300.0}
    app = create_app(mm)
    client = app.test_client()
    resp = client.post(
        "/api/calculate",
        json={"product_price": 1000, "weight": 3, "data_type": "黄 金"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["market_price"] == 300.0
    assert body["price_per_gram"] == round(1000.0 / 3.0, 4)
    mm.get_latest_data.assert_called_once_with("黄 金")


def test_api_history_with_mock_market_price():
    mm = MagicMock()
    mm.get_latest_market_price.return_value = 95.0
    app = create_app(mm)
    client = app.test_client()
    resp = client.post(
        "/api/history",
        json={"product_price": 1000, "weight": 10, "data_type": "黄 金"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["price_per_gram"] == 100.0
    assert body["market_price"] == 95.0


def test_api_latest_price_with_data_type():
    mm = MagicMock()
    mm.get_latest_data.return_value = {
        "data_type": "黄 金",
        "recycle_price": 500.0,
        "real_time_price": 505.0,
    }
    app = create_app(mm)
    client = app.test_client()
    resp = client.get("/api/latest-price?data_type=" + quote("黄 金"))
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["data"]["recycle_price"] == 500.0
    mm.get_latest_data.assert_called_once_with("黄 金")


def test_api_latest_price_all_types():
    mm = MagicMock()
    mm.get_latest_data_by_type.return_value = [{"data_type": "XAU", "recycle_price": 1.0}]
    app = create_app(mm)
    client = app.test_client()
    resp = client.get("/api/latest-price")
    assert resp.status_code == 200
    assert resp.get_json()["data"][0]["data_type"] == "XAU"


def test_api_price_overview():
    api_ttl_cache.clear()
    try:
        mm = MagicMock()
        mm.get_price_overview_data.return_value = [_OVERVIEW_ROW]
        app = create_app(mm)
        client = app.test_client()
        resp = client.get("/api/price-overview")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert len(body["data"]) == 1
        assert body["data"][0]["data_type"] == "XAU"
        assert body["data"][0]["change"] == 1.0
        mm.get_price_overview_data.assert_called_once()
    finally:
        api_ttl_cache.clear()


@patch("collectors.exchange_rate.get_usd_cny_rate")
def test_exchange_rate_prefers_cache_over_db(mock_get_usd):
    """USD/CNY 有内存缓存时不应查库。"""
    mock_get_usd.return_value = 7.25
    mm = MagicMock()
    mm.get_latest_exchange_rate.return_value = 7.0
    app = create_app(mm)
    client = app.test_client()
    resp = client.get("/api/exchange-rate?base=USD&target=CNY")
    assert resp.status_code == 200
    assert resp.get_json()["rate"] == 7.25
    mm.get_latest_exchange_rate.assert_not_called()
