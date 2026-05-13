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
