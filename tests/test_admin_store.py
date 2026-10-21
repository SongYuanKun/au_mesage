from unittest.mock import MagicMock

import pytest

from db.admin_store import AdminStore


def build_store():
    pool = MagicMock()
    connection = pool.get_connection.return_value
    cursor = connection.cursor.return_value
    return AdminStore(pool), connection, cursor


def test_upsert_source_config_uses_one_transaction():
    store, connection, cursor = build_store()
    cursor.fetchone.side_effect = [
        {"source_id": "gold_api", "enabled": 1, "priority": 10},
        {
            "source_id": "gold_api",
            "enabled": 0,
            "priority": 20,
            "updated_at": "2026-07-29 12:00:00",
            "updated_by": "admin",
        },
    ]

    result = store.upsert_data_source_config(
        "gold_api",
        enabled=False,
        priority=20,
        changed_by="admin",
    )

    assert cursor.execute.call_count == 4
    connection.commit.assert_called_once_with()
    connection.rollback.assert_not_called()
    assert result["before"]["enabled"] is True
    assert result["after"]["enabled"] is False


def test_history_failure_rolls_back_current_config():
    store, connection, cursor = build_store()
    cursor.fetchone.return_value = {
        "source_id": "gold_api",
        "enabled": 1,
        "priority": 10,
    }
    cursor.execute.side_effect = [None, None, RuntimeError("history failed")]

    with pytest.raises(RuntimeError, match="history failed"):
        store.upsert_data_source_config(
            "gold_api",
            enabled=False,
            priority=20,
            changed_by="admin",
        )

    connection.rollback.assert_called_once_with()
    connection.commit.assert_not_called()


def test_missing_after_row_rolls_back_transaction():
    store, connection, cursor = build_store()
    cursor.fetchone.side_effect = [
        {"source_id": "gold_api", "enabled": 1, "priority": 10},
        None,
    ]

    with pytest.raises(RuntimeError, match="updated row"):
        store.upsert_data_source_config(
            "gold_api",
            enabled=False,
            priority=20,
            changed_by="admin",
        )

    connection.rollback.assert_called_once_with()
    connection.commit.assert_not_called()
