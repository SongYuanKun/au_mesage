# AU P0 Reliability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make runtime data-source configuration effective, propagate real collection and persistence failures into backoff, and commit data-source configuration plus history atomically.

**Architecture:** Keep the current Flask, MySQL, and in-process collector model. `CollectorManager` reconciles a source-keyed runtime set every 60 seconds; collectors distinguish partial success from total failure; the database layer re-raises failures and performs each administrative update in one transaction.

**Tech Stack:** Python 3.9-compatible syntax, Flask, `mysql.connector`, `threading`, pytest, `unittest.mock`, Ruff.

## Global Constraints

- Scope is limited to runtime source enable/disable, collection and write failure semantics, and atomic source configuration history.
- A committed source enable/disable change must converge in one process within 60 seconds without a restart.
- One `source_id` may have at most one managed runtime instance.
- Successful public API response structures and database schemas must not change.
- No new service, queue, frontend change, or database migration.
- Existing unrelated medium-priority defects remain out of scope.
- Each behavior change follows red-green-refactor TDD and receives an independent review gate.
- Do not read or log credentials, Tokens, `.env` contents, private keys, or complete request secrets.

---

## File Structure

### Create

- `src/collectors/errors.py`: defines the small domain exception used when a collector cannot produce a trustworthy result.
- `tests/test_collector_manager.py`: tests runtime reconciliation, idempotency, retry, and shutdown.
- `tests/test_collectors_failures.py`: tests total failure, partial success, and side-effect collector write propagation.
- `tests/test_db_base.py`: tests rollback and re-raising for all database exceptions.
- `tests/test_admin_store.py`: tests the single-transaction administrative update.

### Modify

- `src/collectors/manager.py`: owns the source-keyed running set and reconciliation thread.
- `src/collectors/base.py`: makes start/stop idempotent and waits for a collector thread to exit before lifecycle completion.
- `src/collectors/gold_api.py`: accepts partial upstream success and raises on total failure.
- `src/collectors/exchange_rate.py`: raises on request, parse, validation, or database failure.
- `src/collectors/fawazahmed0.py`: accepts partial upstream success, raises on total failure, and never swallows a database write error.
- `src/db/base.py`: rolls back and re-raises any database-operation exception; query helpers no longer hide failures.
- `src/db/price_writer.py`: logs and re-raises write failures through `BaseDB`.
- `src/db/admin_store.py`: updates the current row and history row with one cursor and one commit.
- `src/routes/api/admin_routes.py`: rejects an update result without an `after` row.
- `tests/test_base_collector.py`: proves a batch write failure enters collector failure accounting.
- `tests/test_price_writer.py`: proves batch insert failure propagates.
- `tests/test_price_writer_upsert.py`: proves exchange-rate and OHLC write failures propagate.
- `tests/test_admin_sources.py`: proves storage exceptions and invalid update results return HTTP 500.

---

### Task 1: Thread-safe collector runtime reconciliation

**Files:**

- Create: `tests/test_collector_manager.py`
- Modify: `src/collectors/manager.py:1-60`
- Modify: `src/collectors/base.py:32-45`
- Test: `tests/test_collector_manager.py`
- Test: `tests/test_base_collector.py`

**Interfaces:**

- Consumes: `config_cache.bind_db(mysql_manager)`, `config_cache.refresh(force=True)`, and collector instances exposing `start()`, `stop()`, and `name`.
- Produces: `CollectorManager(mysql_manager, *, collector_factories=None, config_cache=source_config_cache, reconcile_interval=60)`, `reconcile_once() -> None`, `collectors -> list`, idempotent `start_all() -> None`, and retryable `stop_all() -> None`.
- Produces: `BaseCollector.stop(join_timeout: float = 20.0) -> None`, which returns only after the worker exits or raises `RuntimeError`.

- [ ] **Step 1: Write failing reconciliation and lifecycle tests**

Create `tests/test_collector_manager.py` with mutable configuration and injected factories:

```python
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
```

Append this test to `tests/test_base_collector.py`:

```python
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
```

- [ ] **Step 2: Run the new tests and verify the current one-shot manager fails**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q -p no:cacheprovider tests/test_collector_manager.py tests/test_base_collector.py
```

Expected: FAIL because `CollectorManager` does not accept injected factories or expose `reconcile_once()`, and `BaseCollector.stop()` does not accept `join_timeout`.

- [ ] **Step 3: Implement the source-keyed manager and terminating lifecycle**

Replace the one-shot list setup in `src/collectors/manager.py` with the following structure:

```python
import logging
import os
import threading
from typing import Callable, Dict, Mapping, Optional

from collectors.base import BaseCollector
from collectors.exchange_rate import ExchangeRateCollector
from collectors.fawazahmed0 import Fawazahmed0Collector
from collectors.gold_api import GoldAPICollector
from collectors.source_config import source_config_cache

logger = logging.getLogger(__name__)

CollectorFactory = Callable[[], BaseCollector]


class CollectorManager:
    def __init__(
        self,
        mysql_manager,
        *,
        collector_factories: Optional[Mapping[str, CollectorFactory]] = None,
        config_cache=source_config_cache,
        reconcile_interval: float = 60,
    ):
        self.mysql_manager = mysql_manager
        self._config_cache = config_cache
        self._config_cache.bind_db(mysql_manager)
        factories = (
            collector_factories
            if collector_factories is not None
            else self._default_factories()
        )
        self._factories = dict(factories)
        self._reconcile_interval = reconcile_interval
        self._collectors: Dict[str, BaseCollector] = {}
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._reconcile_thread = None

    def _default_factories(self) -> Mapping[str, CollectorFactory]:
        def create_playwright():
            from collectors.playwright_collector import PlaywrightCollector

            return PlaywrightCollector(self.mysql_manager)

        return {
            "gold_api": lambda: GoldAPICollector(self.mysql_manager),
            "exchange_rate": lambda: ExchangeRateCollector(self.mysql_manager),
            "fawazahmed0": lambda: Fawazahmed0Collector(self.mysql_manager),
            "playwright": create_playwright,
        }

    @property
    def collectors(self) -> list:
        with self._lock:
            return list(self._collectors.values())

    def _desired_source_ids(self) -> set:
        rows = self._config_cache.refresh(force=True)
        desired = {
            row["source_id"]
            for row in rows
            if row.get("enabled") and row.get("source_id") in self._factories
        }
        if os.environ.get("ENABLE_PLAYWRIGHT", "true").lower() == "false":
            desired.discard("playwright")
        return desired

    def _reconcile_locked(self) -> None:
        desired = self._desired_source_ids()
        running = set(self._collectors)

        for source_id in sorted(running - desired):
            collector = self._collectors[source_id]
            try:
                collector.stop()
            except Exception:
                logger.exception("停止数据源 %s 失败，将在下一轮重试", source_id)
                continue
            del self._collectors[source_id]

        if self._stop_event.is_set():
            return

        for source_id in sorted(desired - set(self._collectors)):
            collector = None
            try:
                collector = self._factories[source_id]()
                collector.start()
            except Exception:
                logger.exception("启动数据源 %s 失败，将在下一轮重试", source_id)
                if collector is not None:
                    try:
                        collector.stop()
                    except Exception:
                        logger.exception("清理启动失败的数据源 %s 时再次失败", source_id)
                continue
            self._collectors[source_id] = collector

        logger.info(
            "运行中的采集器: %s",
            sorted(self._collectors),
        )

    def reconcile_once(self) -> None:
        with self._lock:
            if self._stop_event.is_set():
                return
            self._reconcile_locked()

    def _reconcile_loop(self) -> None:
        while not self._stop_event.wait(self._reconcile_interval):
            try:
                self.reconcile_once()
            except Exception:
                logger.exception("数据源运行集合对账失败")

    def start_all(self) -> None:
        with self._lock:
            if self._reconcile_thread is not None and self._reconcile_thread.is_alive():
                return
            self._stop_event.clear()
            self._reconcile_locked()
            thread = threading.Thread(
                target=self._reconcile_loop,
                name="collector-reconciler",
                daemon=True,
            )
            self._reconcile_thread = thread
            thread.start()

    def stop_all(self) -> None:
        self._stop_event.set()
        thread = self._reconcile_thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=20)

        with self._lock:
            for source_id in list(self._collectors):
                collector = self._collectors[source_id]
                try:
                    collector.stop()
                except Exception:
                    logger.exception("关闭数据源 %s 失败", source_id)
                    continue
                del self._collectors[source_id]
            if thread is None or not thread.is_alive():
                self._reconcile_thread = None
```

Update `BaseCollector.start()` and `BaseCollector.stop()` in `src/collectors/base.py`:

```python
    def start(self):
        if self.is_running:
            return
        if self._thread is not None and self._thread.is_alive():
            raise RuntimeError(f"[{self.name}] 上一个采集线程仍在运行")
        self.is_running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"[{self.name}] 采集器已启动，间隔 {self.interval}s")

    def stop(self, join_timeout: float = 20.0):
        self.is_running = False
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=join_timeout)
            if thread.is_alive():
                raise RuntimeError(f"[{self.name}] 采集线程未在 {join_timeout}s 内退出")
        self._thread = None
        logger.info(f"[{self.name}] 采集器已停止")
```

- [ ] **Step 4: Run lifecycle tests and the application factory regression**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q -p no:cacheprovider tests/test_collector_manager.py tests/test_base_collector.py tests/test_app_factory.py
```

Expected: all selected tests PASS, and the test process exits without a live reconciliation thread.

- [ ] **Step 5: Commit the independently working lifecycle change**

```bash
git add src/collectors/manager.py src/collectors/base.py tests/test_collector_manager.py tests/test_base_collector.py
git commit -m "fix: reconcile collector runtime configuration"
```

---

### Task 2: Trustworthy collector failure semantics

**Files:**

- Create: `src/collectors/errors.py`
- Create: `tests/test_collectors_failures.py`
- Modify: `src/collectors/gold_api.py:30-60`
- Modify: `src/collectors/exchange_rate.py:33-60`
- Modify: `src/collectors/fawazahmed0.py:28-68`

**Interfaces:**

- Consumes: `BaseCollector.fetch() -> list` and the existing MySQL manager write methods.
- Produces: `CollectionError(RuntimeError)`.
- Produces: partial upstream success as a normal return and total upstream failure as `CollectionError`.
- Produces: immediate propagation of `upsert_exchange_rate()` and `upsert_daily_ohlc()` exceptions.

- [ ] **Step 1: Write failing total-failure, partial-success, and write-failure tests**

Create `tests/test_collectors_failures.py`:

```python
import json
from unittest.mock import MagicMock
from urllib.error import URLError

import pytest

from collectors.errors import CollectionError
from collectors.exchange_rate import ExchangeRateCollector
from collectors.fawazahmed0 import Fawazahmed0Collector
from collectors.gold_api import GoldAPICollector


def response_with(payload):
    response = MagicMock()
    response.__enter__.return_value = response
    response.read.return_value = json.dumps(payload).encode("utf-8")
    return response


def test_gold_api_returns_valid_partial_result(monkeypatch):
    manager = MagicMock()
    collector = GoldAPICollector(manager)
    success = response_with({"price": 31.25})
    monkeypatch.setattr(
        "collectors.gold_api.urlopen",
        MagicMock(
            side_effect=[
                URLError("xau down"),
                success,
                URLError("xpt down"),
                URLError("xpd down"),
            ]
        ),
    )

    rows = collector.fetch()

    assert len(rows) == 1
    assert rows[0]["data_type"] == "XAG"
    assert rows[0]["real_time_price"] == 31.25


def test_gold_api_raises_when_every_symbol_fails(monkeypatch):
    collector = GoldAPICollector(MagicMock())
    monkeypatch.setattr(
        "collectors.gold_api.urlopen",
        MagicMock(side_effect=[URLError("down")] * 4),
    )

    with pytest.raises(CollectionError, match="gold_api"):
        collector.fetch()


def test_exchange_rate_raises_on_invalid_response(monkeypatch):
    collector = ExchangeRateCollector(MagicMock())
    monkeypatch.setattr(
        "collectors.exchange_rate.urlopen",
        MagicMock(return_value=response_with({"result": "error"})),
    )

    with pytest.raises(CollectionError, match="exchange_rate"):
        collector.fetch()


def test_exchange_rate_propagates_database_failure(monkeypatch):
    manager = MagicMock()
    manager.upsert_exchange_rate.side_effect = RuntimeError("db unavailable")
    collector = ExchangeRateCollector(manager)
    monkeypatch.setattr(
        "collectors.exchange_rate.urlopen",
        MagicMock(
            return_value=response_with(
                {"result": "success", "rates": {"CNY": 7.25}}
            )
        ),
    )

    with pytest.raises(RuntimeError, match="db unavailable"):
        collector.fetch()


def test_fawaz_accepts_one_successful_symbol(monkeypatch):
    manager = MagicMock()
    xau = response_with(
        {"date": "2026-07-29", "xau": {"cny": 23000, "usd": 3200}}
    )
    monkeypatch.setattr(
        "collectors.fawazahmed0.urlopen",
        MagicMock(side_effect=[xau, URLError("xag down")]),
    )
    collector = Fawazahmed0Collector(manager)

    assert collector.fetch() == []
    assert manager.upsert_daily_ohlc.call_count == 2


def test_fawaz_raises_when_every_symbol_fails(monkeypatch):
    collector = Fawazahmed0Collector(MagicMock())
    monkeypatch.setattr(
        "collectors.fawazahmed0.urlopen",
        MagicMock(side_effect=[URLError("down")] * 2),
    )

    with pytest.raises(CollectionError, match="fawazahmed0"):
        collector.fetch()


def test_fawaz_propagates_database_failure(monkeypatch):
    manager = MagicMock()
    manager.upsert_daily_ohlc.side_effect = RuntimeError("db unavailable")
    collector = Fawazahmed0Collector(manager)
    monkeypatch.setattr(
        "collectors.fawazahmed0.urlopen",
        MagicMock(
            return_value=response_with(
                {"date": "2026-07-29", "xau": {"cny": 23000, "usd": 3200}}
            )
        ),
    )

    with pytest.raises(RuntimeError, match="db unavailable"):
        collector.fetch()
```

- [ ] **Step 2: Run the focused collector tests and verify swallowed failures**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q -p no:cacheprovider tests/test_collectors_failures.py
```

Expected: collection fails because `collectors.errors` does not exist. After creating only the exception file, the total-failure and database-failure assertions still FAIL against the current collectors.

- [ ] **Step 3: Add the domain exception and implement explicit success counting**

Create `src/collectors/errors.py`:

```python
class CollectionError(RuntimeError):
    """A collector could not produce a trustworthy result for this cycle."""
```

In `src/collectors/gold_api.py`, import `CollectionError`, retain valid partial results, and raise if no symbol produced a row:

```python
    def fetch(self) -> list:
        results = []
        failures = []
        date_str = self.today_str()
        time_str = self.time_str()

        for data_type, symbol in SYMBOLS:
            try:
                url = BASE_URL.format(symbol=symbol)
                req = Request(url, headers={"User-Agent": "au-mesage/1.0"})
                with urlopen(req, timeout=10) as resp:
                    body = json.loads(resp.read().decode())
                price = float(body.get("price", 0))
                if price <= 0:
                    raise ValueError("price must be positive")
                results.append(
                    {
                        "trade_date": date_str,
                        "trade_time": time_str,
                        "data_type": data_type,
                        "real_time_price": price,
                        "recycle_price": price,
                        "high_price": 0,
                        "low_price": 0,
                        "source": self.name,
                        "currency": "USD",
                    }
                )
            except Exception as exc:
                failures.append(symbol)
                logger.warning("[%s] 获取 %s 失败: %s", self.name, symbol, exc)

        if not results:
            raise CollectionError(
                f"{self.name}: all upstream symbols failed ({','.join(failures)})"
            )
        return results
```

In `src/collectors/exchange_rate.py`, wrap only request, parse, and validation as collection failure; keep the database call outside that block:

```python
    def fetch(self) -> list:
        try:
            req = Request(BASE_URL, headers={"User-Agent": "au-mesage/1.0"})
            with urlopen(req, timeout=10) as resp:
                body = json.loads(resp.read().decode())
            if body.get("result") != "success":
                raise ValueError(f"unexpected result: {body.get('result')}")
            cny_rate = float(body.get("rates", {}).get("CNY", 0))
            if cny_rate <= 0:
                raise ValueError("CNY rate must be positive")
        except Exception as exc:
            raise CollectionError(f"{self.name}: rate request failed") from exc

        self.mysql_manager.upsert_exchange_rate(
            "USD",
            "CNY",
            cny_rate,
            self.name,
        )
        with _rate_cache["lock"]:
            _rate_cache["USD_CNY"] = cny_rate
        logger.info("[%s] USD/CNY = %s", self.name, cny_rate)
        return []
```

Update the cache only after the database write succeeds, so an unpersisted rate is not advertised as the latest durable rate.

In `src/collectors/fawazahmed0.py`, parse each symbol before writing it, count symbols with at least one valid target, and leave database writes outside the per-symbol exception block:

```python
    def fetch(self) -> list:
        date_str = self.today_str()
        successful_symbols = 0
        failed_symbols = []

        for symbol, target_currencies in SYMBOLS:
            try:
                url = BASE_URL.format(symbol=symbol.lower())
                req = Request(url, headers={"User-Agent": "au-mesage/1.0"})
                with urlopen(req, timeout=15) as resp:
                    body = json.loads(resp.read().decode())
                symbol_data = body.get(symbol.lower(), {})
                api_date = body.get("date", date_str)
                parsed_rates = []
                for currency in target_currencies:
                    raw_rate = symbol_data.get(currency)
                    if raw_rate is None:
                        continue
                    price = float(raw_rate)
                    if price <= 0:
                        continue
                    parsed_rates.append((currency, price))
                if not parsed_rates:
                    raise ValueError("no positive target rate")
            except Exception as exc:
                failed_symbols.append(symbol)
                logger.warning("[%s] 获取 %s 失败: %s", self.name, symbol, exc)
                continue

            for currency, price in parsed_rates:
                self.mysql_manager.upsert_daily_ohlc(
                    trade_date=api_date,
                    data_type=symbol,
                    source=self.name,
                    currency=currency.upper(),
                    open_price=price,
                    high_price=price,
                    low_price=price,
                    close_price=price,
                )
            successful_symbols += 1
            logger.info(
                "[%s] %s 日线数据已写入，日期 %s",
                self.name,
                symbol,
                api_date,
            )

        if successful_symbols == 0:
            raise CollectionError(
                f"{self.name}: all upstream symbols failed "
                f"({','.join(failed_symbols)})"
            )
        return []
```

- [ ] **Step 4: Run collector failure tests and existing exchange regressions**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q -p no:cacheprovider tests/test_collectors_failures.py tests/test_exchange.py tests/test_app_factory.py
```

Expected: all selected tests PASS.

- [ ] **Step 5: Commit the independently working collector semantics**

```bash
git add src/collectors/errors.py src/collectors/gold_api.py src/collectors/exchange_rate.py src/collectors/fawazahmed0.py tests/test_collectors_failures.py
git commit -m "fix: surface collector cycle failures"
```

---

### Task 3: Database write propagation and collector backoff

**Files:**

- Create: `tests/test_db_base.py`
- Modify: `src/db/base.py:1-57`
- Modify: `src/db/price_writer.py:12-72`
- Modify: `tests/test_base_collector.py`
- Modify: `tests/test_price_writer.py`
- Modify: `tests/test_price_writer_upsert.py`

**Interfaces:**

- Consumes: existing `ConnectionPool.get_connection()` and cursor context usage.
- Produces: `BaseDB.get_cursor()` that commits once on success and rolls back, closes, and re-raises on every `Exception`.
- Produces: `_exec()`, `_exec_one()`, and `_exec_value()` that preserve query results but never translate database exceptions into empty values.
- Produces: `PriceWriter` methods that propagate persistence failure to `BaseCollector._run()`.

- [ ] **Step 1: Write failing database propagation tests**

Create `tests/test_db_base.py`:

```python
from unittest.mock import MagicMock

import pytest

from db.base import BaseDB


def test_get_cursor_rolls_back_and_reraises_unknown_exception():
    pool = MagicMock()
    connection = pool.get_connection.return_value
    database = BaseDB(pool)

    with pytest.raises(RuntimeError, match="db unavailable"):
        with database.get_cursor() as _cursor:
            raise RuntimeError("db unavailable")

    connection.rollback.assert_called_once_with()
    connection.commit.assert_not_called()
    connection.close.assert_called_once_with()


def test_exec_does_not_translate_query_failure_to_empty_list():
    pool = MagicMock()
    cursor = pool.get_connection.return_value.cursor.return_value
    cursor.execute.side_effect = RuntimeError("query failed")
    database = BaseDB(pool)

    with pytest.raises(RuntimeError, match="query failed"):
        database._exec("SELECT 1")
```

Append to `tests/test_price_writer.py`:

```python
def test_batch_insert_failure_propagates():
    mock_pool = MagicMock()
    writer = PriceWriter(mock_pool)
    cursor = mock_pool.get_connection.return_value.cursor.return_value
    cursor.executemany.side_effect = RuntimeError("batch failed")
    data = [
        {
            "trade_date": "2026-05-13",
            "trade_time": "10:00:00",
            "data_type": "XAU",
            "real_time_price": 100.0,
            "recycle_price": 99.0,
        }
    ]

    with pytest.raises(RuntimeError, match="batch failed"):
        writer.batch_insert_data(data)
```

Add `import pytest` to that test file.

Append to `tests/test_price_writer_upsert.py`:

```python
def test_upsert_exchange_rate_failure_propagates():
    mock_pool = MagicMock()
    writer = PriceWriter(mock_pool)
    cursor = mock_pool.get_connection.return_value.cursor.return_value
    cursor.execute.side_effect = RuntimeError("exchange write failed")

    with pytest.raises(RuntimeError, match="exchange write failed"):
        writer.upsert_exchange_rate("USD", "CNY", 7.0, "test")


def test_upsert_daily_ohlc_failure_propagates():
    mock_pool = MagicMock()
    writer = PriceWriter(mock_pool)
    cursor = mock_pool.get_connection.return_value.cursor.return_value
    cursor.execute.side_effect = RuntimeError("ohlc write failed")

    with pytest.raises(RuntimeError, match="ohlc write failed"):
        writer.upsert_daily_ohlc(
            "2026-05-13",
            "XAU",
            "gold_api",
            "CNY",
            100,
            110,
            90,
            105,
            1000,
        )
```

Add `import pytest` to that test file.

Append to `tests/test_base_collector.py`:

```python
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
```

- [ ] **Step 2: Run focused tests and verify the current exception swallowing**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q -p no:cacheprovider tests/test_db_base.py tests/test_price_writer.py tests/test_price_writer_upsert.py tests/test_base_collector.py
```

Expected: FAIL because `BaseDB` does not roll back `RuntimeError`, query helpers return empty values, and `PriceWriter` suppresses write failures.

- [ ] **Step 3: Make the transaction context and query helpers transparent**

Replace `BaseDB.get_cursor()` exception handling in `src/db/base.py`:

```python
    @contextmanager
    def get_cursor(self, dictionary=True):
        conn = None
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor(dictionary=dictionary)
            yield cursor
            conn.commit()
        except Exception:
            if conn:
                conn.rollback()
            logging.exception("数据库操作失败")
            raise
        finally:
            if conn:
                conn.close()
```

Remove the catch-and-default behavior from all three query helpers:

```python
    def _exec(self, query, params=None, dictionary=True):
        with self.get_cursor(dictionary=dictionary) as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()

    def _exec_one(self, query, params=None):
        with self.get_cursor(dictionary=True) as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()

    def _exec_value(self, query, params=None):
        with self.get_cursor(dictionary=False) as cursor:
            cursor.execute(query, params or ())
            row = cursor.fetchone()
            return row[0] if row else None
```

Remove the three `try/except` wrappers in `src/db/price_writer.py`. Each method should execute through `get_cursor()` directly:

```python
        with self.get_cursor() as cursor:
            cursor.executemany(query, values)
        logging.info("成功插入 %s 条数据", len(data_list))
```

```python
        with self.get_cursor() as cursor:
            cursor.execute(query, (base, target, rate, source))
```

```python
        with self.get_cursor() as cursor:
            cursor.execute(
                query,
                (
                    trade_date,
                    data_type,
                    source,
                    currency,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    volume,
                ),
            )
```

Do not add another catch in `BaseCollector`; its existing `try/except` already records failure after any `fetch()` or batch-write exception.

- [ ] **Step 4: Run focused propagation tests and collector regressions**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q -p no:cacheprovider tests/test_db_base.py tests/test_price_writer.py tests/test_price_writer_upsert.py tests/test_base_collector.py tests/test_collectors_failures.py
```

Expected: all selected tests PASS. The batch-write test must call `record_failure("dummy")` and must not call `record_success`.

- [ ] **Step 5: Commit the independently working error propagation**

```bash
git add src/db/base.py src/db/price_writer.py tests/test_db_base.py tests/test_price_writer.py tests/test_price_writer_upsert.py tests/test_base_collector.py
git commit -m "fix: propagate database write failures"
```

---

### Task 4: Atomic administrative source updates

**Files:**

- Create: `tests/test_admin_store.py`
- Modify: `src/db/admin_store.py:40-79`
- Modify: `src/routes/api/admin_routes.py:1-79`
- Modify: `tests/test_admin_sources.py`

**Interfaces:**

- Consumes: Task 3's `BaseDB.get_cursor(dictionary=True)` commit, rollback, and re-raise contract.
- Produces: `AdminStore.upsert_data_source_config(...) -> {"before": Optional[dict], "after": dict}` with four statements in one transaction.
- Produces: HTTP 500 with error code `INTERNAL` when storage raises or no updated row is returned.
- Preserves: the existing HTTP 200 response body and audit behavior on success.

- [ ] **Step 1: Write failing single-transaction and HTTP failure tests**

Create `tests/test_admin_store.py`:

```python
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
```

Append to `tests/test_admin_sources.py`:

```python
def test_update_source_returns_internal_error_on_storage_failure(admin_client):
    client, mm, headers = admin_client
    mm.upsert_data_source_config.side_effect = RuntimeError("db unavailable")

    resp = client.put(
        "/api/admin/sources/gold_api",
        json={"enabled": False, "priority": 10},
        headers=headers,
    )

    assert resp.status_code == 500
    assert resp.get_json()["error"]["code"] == "INTERNAL"
    mm.insert_audit_log.assert_not_called()


def test_update_source_rejects_missing_after_row(admin_client):
    client, mm, headers = admin_client
    mm.upsert_data_source_config.return_value = {
        "before": {"source_id": "gold_api", "enabled": True, "priority": 10},
        "after": None,
    }

    resp = client.put(
        "/api/admin/sources/gold_api",
        json={"enabled": False, "priority": 10},
        headers=headers,
    )

    assert resp.status_code == 500
    assert resp.get_json()["error"]["code"] == "INTERNAL"
    mm.insert_audit_log.assert_not_called()
```

- [ ] **Step 2: Run focused administrative tests and verify partial commits remain possible**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q -p no:cacheprovider tests/test_admin_store.py tests/test_admin_sources.py
```

Expected: FAIL because `AdminStore` obtains and commits separate cursors, suppresses the history failure through `_exec()`, and the route accepts `after=None`.

- [ ] **Step 3: Execute all four statements with one cursor**

Replace `AdminStore.upsert_data_source_config()` in `src/db/admin_store.py` with one cursor context:

```python
    def upsert_data_source_config(
        self,
        source_id: str,
        *,
        enabled: bool,
        priority: int,
        changed_by: str,
    ) -> Dict[str, Any]:
        with self.get_cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT source_id, enabled, priority "
                "FROM data_source_config WHERE source_id = %s",
                (source_id,),
            )
            before = cursor.fetchone()
            cursor.execute(
                """
                INSERT INTO data_source_config
                  (source_id, enabled, priority, updated_by)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  enabled = VALUES(enabled),
                  priority = VALUES(priority),
                  updated_by = VALUES(updated_by)
                """,
                (source_id, 1 if enabled else 0, priority, changed_by),
            )
            cursor.execute(
                """
                INSERT INTO data_source_config_history
                  (source_id, enabled, priority, changed_by)
                VALUES (%s, %s, %s, %s)
                """,
                (source_id, 1 if enabled else 0, priority, changed_by),
            )
            cursor.execute(
                """
                SELECT source_id, enabled, priority, updated_at, updated_by
                FROM data_source_config
                WHERE source_id = %s
                """,
                (source_id,),
            )
            after = cursor.fetchone()
            if after is None:
                raise RuntimeError(
                    f"data source {source_id} updated row could not be read"
                )

        after["enabled"] = bool(after.get("enabled"))
        if before:
            before["enabled"] = bool(before.get("enabled"))
        return {"before": before, "after": after}
```

No helper inside this method may open another cursor. `rollback_data_source_config()` may retain its history lookup followed by this atomic upsert because the state-changing current-row and history-row writes remain in the same transaction.

- [ ] **Step 4: Reject invalid storage results before cache invalidation and audit**

In `src/routes/api/admin_routes.py`, validate the result immediately after the storage call:

```python
        result = mysql_manager.upsert_data_source_config(
            source_id,
            enabled=enabled,
            priority=priority,
            changed_by=get_actor(),
        )
        if result.get("after") is None:
            raise ApiError.internal("数据源配置保存失败")
        source_config_cache.invalidate()
```

Apply the same invariant after `rollback_data_source_config()` returns a non-`None` result:

```python
        if result is None:
            raise ApiError.not_found("无可回滚的历史版本")
        if result.get("after") is None:
            raise ApiError.internal("数据源配置回滚失败")
```

Keep cache invalidation and `log_audit()` after these checks.

- [ ] **Step 5: Run administrative tests and the complete Python suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q -p no:cacheprovider tests/test_admin_store.py tests/test_admin_sources.py tests/test_audit.py tests/test_auth.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q -p no:cacheprovider
```

Expected: both commands PASS. The full suite contains the original 60 tests plus all newly added tests.

- [ ] **Step 6: Run lint, traceability, and the targeted Flask failure probe**

Run Ruff only on changed Python files because the repository has one unrelated baseline warning:

```bash
.venv/bin/ruff check --no-cache \
  src/collectors/manager.py \
  src/collectors/base.py \
  src/collectors/errors.py \
  src/collectors/gold_api.py \
  src/collectors/exchange_rate.py \
  src/collectors/fawazahmed0.py \
  src/db/base.py \
  src/db/price_writer.py \
  src/db/admin_store.py \
  src/routes/api/admin_routes.py \
  tests/test_collector_manager.py \
  tests/test_collectors_failures.py \
  tests/test_db_base.py \
  tests/test_admin_store.py \
  tests/test_base_collector.py \
  tests/test_price_writer.py \
  tests/test_price_writer_upsert.py \
  tests/test_admin_sources.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/rtm_traceability_check.py
```

Expected: Ruff exits 0 for all changed files and RTM reports `RTM 追踪校验通过（4 条高优需求）`.

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python - <<'PY'
import os
from unittest.mock import MagicMock

from route import create_app

os.environ["AUTH_ENABLED"] = "true"
os.environ["AUTH_ADMIN_TOKEN"] = "probe-token"
manager = MagicMock()
manager.upsert_data_source_config.side_effect = RuntimeError("db unavailable")
client = create_app(manager).test_client()
response = client.put(
    "/api/admin/sources/gold_api",
    json={"enabled": False, "priority": 10},
    headers={"Authorization": "Bearer probe-token"},
)
body = response.get_json()
print(response.status_code, body["error"]["code"])
PY
```

Expected output: `500 INTERNAL`.

- [ ] **Step 7: Commit the atomic administrative update**

```bash
git add src/db/admin_store.py src/routes/api/admin_routes.py tests/test_admin_store.py tests/test_admin_sources.py
git commit -m "fix: make source configuration updates atomic"
```

- [ ] **Step 8: Record final evidence for review**

Run:

```bash
git status --short --branch
git log --oneline --decorate -5
git diff --check github/main...HEAD
```

Expected: no uncommitted implementation files, four focused implementation commits after the design and plan commits, and no whitespace errors. Report the exact test count, targeted Ruff result, RTM result, known unrelated full-Ruff warning, and changed-file list to the reviewer.
