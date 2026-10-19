import threading
from unittest.mock import MagicMock

import collectors.playwright_collector as playwright_module
from collectors.playwright_collector import PlaywrightCollector


def use_fake_playwright(monkeypatch, browser=None, launch_error=None):
    session = MagicMock()
    launch = session.__enter__.return_value.chromium.launch
    if launch_error is not None:
        launch.side_effect = launch_error
    else:
        launch.return_value = browser
    monkeypatch.setattr(playwright_module, "sync_playwright", MagicMock(return_value=session))


def build_collector(monkeypatch):
    collector = PlaywrightCollector(MagicMock())
    collector.interval = 3600
    monkeypatch.setattr(collector, "_refresh_and_get_data", lambda: [])
    return collector


def test_stop_waits_for_threads_and_closes_browser_in_worker(monkeypatch):
    close_threads = []
    browser = MagicMock()
    browser.close.side_effect = lambda: close_threads.append(threading.current_thread())
    use_fake_playwright(monkeypatch, browser=browser)
    collector = build_collector(monkeypatch)

    collector.start()
    collector.stop(join_timeout=5)

    assert collector.is_alive() is False
    assert len(close_threads) == 1
    # 浏览器只能在创建它的线程里关闭
    assert close_threads[0] is not threading.current_thread()


def test_start_is_idempotent_while_running(monkeypatch):
    use_fake_playwright(monkeypatch, browser=MagicMock())
    collector = build_collector(monkeypatch)

    collector.start()
    first_thread = collector._thread
    collector.start()
    try:
        assert collector._thread is first_thread
    finally:
        collector.stop(join_timeout=5)


def test_launch_failure_marks_collector_dead(monkeypatch):
    use_fake_playwright(monkeypatch, launch_error=RuntimeError("browser missing"))
    collector = build_collector(monkeypatch)

    collector.start()
    collector._thread.join(timeout=5)
    collector._save_thread.join(timeout=5)

    # 线程退出后应报告未存活，管理器下一轮会重新拉起
    assert collector.is_alive() is False
    assert collector.is_running is False
