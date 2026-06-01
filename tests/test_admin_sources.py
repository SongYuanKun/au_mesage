from unittest.mock import MagicMock

import pytest

from route import create_app


@pytest.fixture
def admin_client(monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_ADMIN_TOKEN", "admin-tok")
    mm = MagicMock()
    mm.list_data_source_configs.return_value = [
        {"source_id": "gold_api", "enabled": True, "priority": 10},
    ]
    app = create_app(mm)
    client = app.test_client()
    headers = {"Authorization": "Bearer admin-tok"}
    return client, mm, headers


def test_list_admin_sources(admin_client):
    client, mm, headers = admin_client
    resp = client.get("/api/admin/sources", headers=headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["data"][0]["source_id"] == "gold_api"
    mm.list_data_source_configs.assert_called()


def test_update_source(admin_client):
    client, mm, headers = admin_client
    mm.upsert_data_source_config.return_value = {
        "before": {"source_id": "gold_api", "enabled": True, "priority": 10},
        "after": {"source_id": "gold_api", "enabled": False, "priority": 10},
    }
    resp = client.put(
        "/api/admin/sources/gold_api",
        json={"enabled": False, "priority": 10},
        headers=headers,
    )
    assert resp.status_code == 200
    mm.upsert_data_source_config.assert_called_once()
    mm.insert_audit_log.assert_called()
