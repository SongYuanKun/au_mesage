from unittest.mock import MagicMock

import pytest

from route import create_app


@pytest.fixture(autouse=True)
def _clear_auth_env(monkeypatch):
    monkeypatch.delenv("AUTH_ENABLED", raising=False)
    monkeypatch.delenv("AUTH_ADMIN_TOKEN", raising=False)


def test_export_open_when_auth_disabled():
    mm = MagicMock()
    mm.query_data.return_value = []
    app = create_app(mm)
    client = app.test_client()
    resp = client.get(
        "/api/export/history?data_type=XAU&start_date=2026-05-01&end_date=2026-05-01"
    )
    assert resp.status_code == 200


def test_export_requires_token_when_auth_enabled(monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_ADMIN_TOKEN", "secret-admin")
    mm = MagicMock()
    app = create_app(mm)
    client = app.test_client()
    resp = client.get(
        "/api/export/history?data_type=XAU&start_date=2026-05-01&end_date=2026-05-01"
    )
    assert resp.status_code == 401
    assert resp.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_export_with_admin_token(monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_ADMIN_TOKEN", "secret-admin")
    mm = MagicMock()
    mm.query_data.return_value = []
    app = create_app(mm)
    client = app.test_client()
    resp = client.get(
        "/api/export/history?data_type=XAU&start_date=2026-05-01&end_date=2026-05-01",
        headers={"Authorization": "Bearer secret-admin"},
    )
    assert resp.status_code == 200
    mm.insert_audit_log.assert_called()


def test_forbidden_admin_api_logs_audit(monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_USER_TOKEN", "user-token")
    mm = MagicMock()
    app = create_app(mm)
    client = app.test_client()
    resp = client.get(
        "/api/admin/sources",
        headers={"Authorization": "Bearer user-token"},
    )
    assert resp.status_code == 403
    assert resp.get_json()["error"]["code"] == "FORBIDDEN"
    mm.insert_audit_log.assert_called()
