import threading
from unittest.mock import MagicMock

from collectors.base import BaseCollector

class DummyCollector(BaseCollector):
    name = "dummy"
    interval = 1
    
    def __init__(self, manager, fetch_mock):
        super().__init__(manager)
        self.fetch_mock = fetch_mock
        
    def fetch(self):
        return self.fetch_mock()

def test_collector_backoff(monkeypatch):
    mock_manager = MagicMock()
    
    # We will control the loop to run 3 times, then exit
    call_count = 0
    
    def fetch_mock():
        nonlocal call_count
        call_count += 1
        if call_count >= 3:
            collector.is_running = False
        raise Exception("Fetch failed")
    
    collector = DummyCollector(mock_manager, fetch_mock)
    collector.is_running = True
    
    sleep_mock = MagicMock()
    monkeypatch.setattr("collectors.base.time.sleep", sleep_mock)
    
    collector._run()
    
    # fetch was called 3 times
    assert call_count == 3
    
    # sleeps should be: 1s, 2s, 4s (total 7 seconds)
    # wait, the sleep loop calls time.sleep(1) N times
    # First fail: current_sleep = min(3600, 1 * 2^0) = 1
    # Second fail: current_sleep = min(3600, 1 * 2^1) = 2
    # Third fail: current_sleep = min(3600, 1 * 2^2) = 4
    # But after 3rd fail, fetch_mock sets is_running = False, so the 3rd sleep loop exits immediately!
    # Let's verify:
    # After 1st fail: sleep(1) called 1 time.
    # After 2nd fail: sleep(1) called 2 times.
    # After 3rd fail: is_running is False, sleep(1) called 0 times.
    # Total sleep calls = 3
    assert sleep_mock.call_count == 3

def test_collector_recovery(monkeypatch):
    mock_manager = MagicMock()
    
    call_count = 0
    
    def fetch_mock():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Fetch failed")
        elif call_count == 2:
            return [{"fake": "data"}]
        else:
            collector.is_running = False
            return []
            
    collector = DummyCollector(mock_manager, fetch_mock)
    collector.is_running = True
    
    sleep_mock = MagicMock()
    monkeypatch.setattr("collectors.base.time.sleep", sleep_mock)
    
    collector._run()
    
    assert call_count == 3
    # 1st fail -> sleep 1
    # 2nd success -> sleep 1
    # 3rd exit -> sleep 0
    assert sleep_mock.call_count == 2
    mock_manager.batch_insert_data.assert_called_once_with([{"fake": "data"}])


def test_stop_waits_for_worker_thread():
    collector = DummyCollector(MagicMock(), MagicMock(return_value=[]))
    worker = MagicMock()
    worker.is_alive.return_value = False
    collector.is_running = True
    collector._thread = worker

    collector.stop(join_timeout=0.25)

    worker.join.assert_called_once_with(timeout=0.25)
    assert collector.is_running is False
    assert collector._thread is None


def test_worker_self_stop_raises_and_blocks_replacement_worker():
    first_worker_ready = threading.Event()
    allow_self_stop = threading.Event()
    self_stop_finished = threading.Event()
    release_first_worker = threading.Event()
    first_worker_holder = []
    replacement_workers = []
    self_stop_errors = []
    self_stop_returned = []

    def fetch_mock():
        current = threading.current_thread()
        if not first_worker_holder:
            first_worker_ready.set()
            allow_self_stop.wait(timeout=1)

        if current is first_worker_holder[0]:
            try:
                collector.stop(join_timeout=0.01)
            except RuntimeError as error:
                self_stop_errors.append(error)
            else:
                self_stop_returned.append(True)
            finally:
                self_stop_finished.set()
            release_first_worker.wait(timeout=1)
            return []

        replacement_workers.append(current)
        collector.is_running = False
        return []

    collector = DummyCollector(MagicMock(), fetch_mock)
    first_worker = None
    replacement_start_error = None
    thread_reference_during_self_stop = None

    try:
        collector.start()
        assert first_worker_ready.wait(timeout=1)
        first_worker = collector._thread
        first_worker_holder.append(first_worker)
        allow_self_stop.set()
        assert self_stop_finished.wait(timeout=1)

        thread_reference_during_self_stop = collector._thread
        try:
            collector.start()
        except RuntimeError as error:
            replacement_start_error = error
    finally:
        release_first_worker.set()
        if first_worker is not None:
            first_worker.join(timeout=1)
        for worker in replacement_workers:
            worker.join(timeout=1)
        collector.stop(join_timeout=0.25)

    assert self_stop_returned == []
    assert len(self_stop_errors) == 1
    assert thread_reference_during_self_stop is first_worker
    assert isinstance(replacement_start_error, RuntimeError)
    assert replacement_workers == []
    assert first_worker.is_alive() is False
    assert collector._thread is None


def test_batch_write_failure_records_failure_and_uses_backoff(monkeypatch):
    mock_manager = MagicMock()
    collector = DummyCollector(mock_manager, MagicMock())
    write_count = 0

    def fetch_data():
        return [{"fake": "data"}]

    def fail_write(_rows):
        nonlocal write_count
        write_count += 1
        if write_count == 3:
            collector.is_running = False
        raise RuntimeError("db unavailable")

    collector.fetch_mock = fetch_data
    mock_manager.batch_insert_data.side_effect = fail_write
    collector.is_running = True
    success = MagicMock()
    failure = MagicMock()
    sleep = MagicMock()
    monkeypatch.setattr("collectors.base.collector_stats.record_success", success)
    monkeypatch.setattr("collectors.base.collector_stats.record_failure", failure)
    monkeypatch.setattr("collectors.base.time.sleep", sleep)

    collector._run()

    assert failure.call_count == 3
    failure.assert_called_with("dummy")
    success.assert_not_called()
    assert sleep.call_count == 3


def test_is_alive_reflects_worker_thread():
    collector = DummyCollector(MagicMock(), MagicMock(return_value=[]))
    assert collector.is_alive() is False

    worker = MagicMock()
    worker.is_alive.return_value = True
    collector._thread = worker
    assert collector.is_alive() is True

    worker.is_alive.return_value = False
    assert collector.is_alive() is False
