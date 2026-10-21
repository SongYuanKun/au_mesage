from unittest.mock import MagicMock

from collectors.source_config import DEFAULT_SOURCES, SourceConfigCache


def build_cache(rows):
    db = MagicMock()
    db.list_data_source_configs.return_value = rows
    cache = SourceConfigCache()
    cache.bind_db(db)
    return cache, db


def test_refresh_keeps_last_loaded_config_when_db_fails():
    disabled = [{"source_id": "gold_api", "enabled": False, "priority": 10}]
    cache, db = build_cache(disabled)
    assert cache.refresh(force=True) == disabled

    db.list_data_source_configs.side_effect = RuntimeError("db unavailable")

    # 数据库短暂故障时不能退回“全部启用”的默认配置，否则会拉起已停用的数据源
    assert cache.refresh(force=True) == disabled
    assert cache.is_enabled("gold_api") is False


def test_refresh_uses_defaults_when_db_fails_before_first_load():
    cache, db = build_cache([])
    db.list_data_source_configs.side_effect = RuntimeError("db unavailable")

    assert cache.refresh(force=True) == DEFAULT_SOURCES
