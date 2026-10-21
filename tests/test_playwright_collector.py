import threading
from unittest.mock import MagicMock

import collectors.playwright_collector as playwright_module
from collectors import stats as collector_stats
from collectors.playwright_collector import PlaywrightCollector


def use_fake_playwright(monkeypatch, browser=None, launch_error=None, browsers=None):
    session = MagicMock()
    launch = session.__enter__.return_value.chromium.launch
    if launch_error is not None:
        launch.side_effect = launch_error
    elif browsers is not None:
        launch.side_effect = browsers
    else:
        launch.return_value = browser
    monkeypatch.setattr(playwright_module, "sync_playwright", MagicMock(return_value=session))
    return launch


def healthy_browser():
    browser = MagicMock()
    browser.is_connected.return_value = True
    browser.new_context.return_value.new_page.return_value.is_closed.return_value = False
    return browser


def build_collector(monkeypatch, refresh=None):
    collector = PlaywrightCollector(MagicMock())
    collector.interval = 3600
    collector.restart_delay = 0.01
    collector.max_restart_delay = 0.05
    collector.retry_delay = 0.01
    monkeypatch.setattr(collector, "_refresh_and_get_data", refresh or (lambda: [{"data_type": "黄 金"}]))
    return collector


def test_stop_waits_for_threads_and_closes_browser_in_worker(monkeypatch):
    close_threads = []
    browser = healthy_browser()
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
    use_fake_playwright(monkeypatch, browser=healthy_browser())
    collector = build_collector(monkeypatch)

    collector.start()
    first_thread = collector._thread
    collector.start()
    try:
        assert collector._thread is first_thread
    finally:
        collector.stop(join_timeout=5)


def test_launch_failure_retries_with_backoff_until_stopped(monkeypatch):
    collector_stats.reset_for_tests()
    retried = threading.Event()
    calls = []

    def failing_launch(*args, **kwargs):
        calls.append(1)
        if len(calls) >= 3:
            retried.set()
        raise RuntimeError("browser missing")

    use_fake_playwright(monkeypatch, launch_error=failing_launch)
    collector = build_collector(monkeypatch)

    collector.start()
    try:
        assert retried.wait(timeout=5)
        # 启动失败不再让线程退出，而是带退避地重建
        assert collector.is_alive() is True
        row = {r["source_id"]: r for r in collector_stats.snapshot()}["playwright"]
        assert row["failure_count"] >= 3
    finally:
        collector.stop(join_timeout=5)
    assert collector.is_alive() is False


def test_closed_page_rebuilds_browser_session(monkeypatch):
    collector_stats.reset_for_tests()
    # 第一个浏览器已断开（生产日志中的 "Target page, context or browser has been closed"）
    dead_browser = MagicMock()
    dead_browser.is_connected.return_value = False
    good_browser = healthy_browser()
    launch = use_fake_playwright(monkeypatch, browsers=[dead_browser, good_browser])

    collected = threading.Event()
    calls = []

    def refresh():
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("Page.reload: Target page, context or browser has been closed")
        collected.set()
        return [{"data_type": "黄 金"}]

    collector = build_collector(monkeypatch, refresh=refresh)
    collector.start()
    try:
        assert collected.wait(timeout=5)
    finally:
        collector.stop(join_timeout=5)

    assert launch.call_count == 2
    dead_browser.close.assert_called_once()
    # stop() 会唤醒保存线程；报价要么仍在缓冲区，要么已交给数据库写入，不能丢失。
    persisted = collector.mysql_manager.batch_insert_data.call_args_list
    assert collector.data_buffer == [{"data_type": "黄 金"}] or persisted
    row = {r["source_id"]: r for r in collector_stats.snapshot()}["playwright"]
    assert row["last_success_at"] is not None


def test_repeated_failures_rebuild_session_even_if_page_open(monkeypatch):
    first, second = healthy_browser(), healthy_browser()
    launch = use_fake_playwright(monkeypatch, browsers=[first, second])
    rebuilt = threading.Event()

    def refresh():
        if launch.call_count >= 2:
            rebuilt.set()
            return [{"data_type": "白 银"}]
        raise RuntimeError("wait_for_selector timeout")

    collector = build_collector(monkeypatch, refresh=refresh)
    collector.max_session_failures = 2
    collector.start()
    try:
        assert rebuilt.wait(timeout=5)
    finally:
        collector.stop(join_timeout=5)

    first.close.assert_called_once()


def test_empty_page_counts_as_failure(monkeypatch):
    collector_stats.reset_for_tests()
    use_fake_playwright(monkeypatch, browser=healthy_browser())
    attempted = threading.Event()

    def refresh():
        attempted.set()
        return []

    collector = build_collector(monkeypatch, refresh=refresh)
    collector.start()
    try:
        assert attempted.wait(timeout=5)
    finally:
        collector.stop(join_timeout=5)

    row = {r["source_id"]: r for r in collector_stats.snapshot()}["playwright"]
    assert row["last_success_at"] is None
    assert row["failure_count"] >= 1


def test_restart_delay_grows_exponentially_to_cap():
    collector = PlaywrightCollector(MagicMock())
    delays = [collector._restart_delay_for(n) for n in range(1, 8)]
    assert delays == [30, 60, 120, 240, 480, 600, 600]


def _quote_row(buyback, selling, high="0"):
    def text(value):
        element = MagicMock()
        element.inner_text.return_value = value
        return element

    name = text("黄 金")
    prices = {2: buyback, 3: selling, 4: high}

    def query(selector):
        if selector == ".symbol-name":
            return name
        for nth, value in prices.items():
            if f"nth-child({nth})" in selector:
                return text(value) if value is not None else None
        return None

    row = MagicMock()
    row.query_selector.side_effect = query
    return row


def test_price_parser_skips_missing_placeholder_and_zero_quotes():
    collector = PlaywrightCollector(MagicMock())
    collector.page = MagicMock()
    collector.page.query_selector_all.return_value = [
        _quote_row(None, "500"),
        _quote_row("--", "500"),
        _quote_row("0", "500"),
        _quote_row("500", "0"),
    ]

    assert collector._refresh_and_get_data() == []


def test_price_parser_keeps_positive_quotes():
    collector = PlaywrightCollector(MagicMock())
    collector.page = MagicMock()
    collector.page.query_selector_all.return_value = [_quote_row("500.5", "501.2", "502")]

    rows = collector._refresh_and_get_data()

    assert len(rows) == 1
    assert rows[0]["recycle_price"] == 500.5
    assert rows[0]["real_time_price"] == 501.2
    assert rows[0]["high_price"] == 502.0
