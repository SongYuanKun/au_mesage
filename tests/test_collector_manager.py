import threading
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


def test_default_reconcile_loop_waits_30_seconds_between_refreshes():
    cache = FakeConfigCache([])
    manager = CollectorManager(
        MagicMock(),
        collector_factories={},
        config_cache=cache,
    )
    stop_event = MagicMock()
    stop_event.wait.return_value = True
    manager._stop_event = stop_event

    manager._reconcile_loop()

    stop_event.wait.assert_called_once_with(30)


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


def test_concurrent_start_during_stop_does_not_leave_hidden_reconciler(
    monkeypatch,
):
    gold = MagicMock(name="gold_collector")
    gold.name = "gold_api"
    manager, _cache = build_manager(
        [{"source_id": "gold_api", "enabled": True}],
        {"gold_api": MagicMock(return_value=gold)},
    )
    real_thread = threading.Thread
    created_reconcile_threads = []

    def recording_thread(*args, **kwargs):
        thread = real_thread(*args, **kwargs)
        created_reconcile_threads.append(thread)
        return thread

    monkeypatch.setattr(
        "collectors.manager.threading.Thread",
        recording_thread,
    )
    manager.start_all()
    first_reconcile_thread = manager._reconcile_thread
    original_join = first_reconcile_thread.join
    reconcile_joined = threading.Event()
    allow_stop_to_finish = threading.Event()

    def pause_after_join(timeout=None):
        original_join(timeout=timeout)
        reconcile_joined.set()
        if not allow_stop_to_finish.wait(timeout=1):
            raise RuntimeError("test timed out while pausing stop_all")

    first_reconcile_thread.join = pause_after_join
    stop_errors = []

    def stop_manager():
        try:
            manager.stop_all()
        except Exception as error:
            stop_errors.append(error)

    stopper = real_thread(target=stop_manager)
    stopper.start()

    try:
        assert reconcile_joined.wait(timeout=1)
        manager.start_all()
        allow_stop_to_finish.set()
        stopper.join(timeout=1)

        manager.reconcile_once()
        stopper_alive = stopper.is_alive()
        manager_thread_reference = manager._reconcile_thread
        active_reconcile_threads = [
            thread
            for thread in created_reconcile_threads
            if thread.is_alive()
        ]
        collector_snapshot = manager.collectors
        collector_start_count = gold.start.call_count
        collector_stop_count = gold.stop.call_count
    finally:
        allow_stop_to_finish.set()
        stop_event = manager._stop_event
        if stop_event is not None:
            stop_event.set()
        for thread in created_reconcile_threads:
            if thread is first_reconcile_thread:
                original_join(timeout=1)
            else:
                thread.join(timeout=1)
        stopper.join(timeout=1)

    assert stopper_alive is False
    assert stop_errors == []
    assert len(created_reconcile_threads) == 1
    assert active_reconcile_threads == []
    assert manager_thread_reference is None
    assert collector_snapshot == []
    assert collector_start_count == 1
    assert collector_stop_count == 1


def test_reconcile_restarts_collector_whose_thread_exited():
    first = MagicMock(name="first_collector")
    first.is_alive.return_value = True
    second = MagicMock(name="second_collector")
    second.is_alive.return_value = True
    factory = MagicMock(side_effect=[first, second])
    manager, _cache = build_manager(
        [{"source_id": "gold_api", "enabled": True}],
        {"gold_api": factory},
    )

    manager.reconcile_once()
    first.is_alive.return_value = False
    manager.reconcile_once()

    first.stop.assert_called_once_with()
    second.start.assert_called_once_with()
    assert manager.collectors == [second]


def test_missing_dependency_is_reported_once_and_not_retried():
    factory = MagicMock(side_effect=ImportError("No module named 'playwright'"))
    manager, _cache = build_manager(
        [{"source_id": "playwright", "enabled": True}],
        {"playwright": factory},
    )

    manager.reconcile_once()
    manager.reconcile_once()

    factory.assert_called_once_with()
    assert manager.collectors == []
