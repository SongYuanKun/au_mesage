from unittest.mock import MagicMock

from collectors.manager import CollectorManager


class FakeConfigCache:
    def __init__(self, rows):
        self.rows = rows
        self.bound_db = None

    def bind_db(self, mysql_manager):
        self.bound_db = mysql_manager

    def refresh(self, force=False):
        return list(self.rows)


def build_manager(rows, factories):
    cache = FakeConfigCache(rows)
    manager = CollectorManager(
        MagicMock(),
        collector_factories=factories,
        config_cache=cache,
        reconcile_interval=3600,
    )
    return manager, cache


def test_reconcile_starts_newly_enabled_source_once():
    gold = MagicMock(name="gold_collector")
    gold.name = "gold_api"
    factory = MagicMock(return_value=gold)
    manager, cache = build_manager(
        [{"source_id": "gold_api", "enabled": False}],
        {"gold_api": factory},
    )

    manager.reconcile_once()
    cache.rows = [{"source_id": "gold_api", "enabled": True}]
    manager.reconcile_once()
    manager.reconcile_once()

    factory.assert_called_once_with()
    gold.start.assert_called_once_with()
    assert manager.collectors == [gold]


def test_reconcile_stops_disabled_source_once():
    gold = MagicMock(name="gold_collector")
    gold.name = "gold_api"
    manager, cache = build_manager(
        [{"source_id": "gold_api", "enabled": True}],
        {"gold_api": MagicMock(return_value=gold)},
    )

    manager.reconcile_once()
    cache.rows = [{"source_id": "gold_api", "enabled": False}]
    manager.reconcile_once()
    manager.reconcile_once()

    gold.stop.assert_called_once_with()
    assert manager.collectors == []


def test_failed_start_is_retried_without_polluting_running_set():
    broken = MagicMock(name="broken_collector")
    broken.name = "gold_api"
    broken.start.side_effect = RuntimeError("start failed")
    healthy = MagicMock(name="healthy_collector")
    healthy.name = "gold_api"
    factory = MagicMock(side_effect=[broken, healthy])
    manager, _cache = build_manager(
        [{"source_id": "gold_api", "enabled": True}],
        {"gold_api": factory},
    )

    manager.reconcile_once()
    assert manager.collectors == []

    manager.reconcile_once()
    assert manager.collectors == [healthy]
    healthy.start.assert_called_once_with()


def test_failed_stop_is_retained_and_retried():
    gold = MagicMock(name="gold_collector")
    gold.name = "gold_api"
    gold.stop.side_effect = [RuntimeError("busy"), None]
    manager, cache = build_manager(
        [{"source_id": "gold_api", "enabled": True}],
        {"gold_api": MagicMock(return_value=gold)},
    )
    manager.reconcile_once()
    cache.rows = [{"source_id": "gold_api", "enabled": False}]

    manager.reconcile_once()
    assert manager.collectors == [gold]

    manager.reconcile_once()
    assert manager.collectors == []
    assert gold.stop.call_count == 2


def test_stop_all_ends_reconcile_thread_and_is_idempotent():
    gold = MagicMock(name="gold_collector")
    gold.name = "gold_api"
    manager, _cache = build_manager(
        [{"source_id": "gold_api", "enabled": True}],
        {"gold_api": MagicMock(return_value=gold)},
    )

    manager.start_all()
    manager.stop_all()
    manager.stop_all()

    gold.start.assert_called_once_with()
    gold.stop.assert_called_once_with()
    assert manager.collectors == []
