import json
from unittest.mock import MagicMock
from urllib.error import URLError

import pytest
from mysql.connector import Error

from collectors.errors import CollectionError
from collectors.exchange_rate import ExchangeRateCollector, _rate_cache
from collectors.fawazahmed0 import Fawazahmed0Collector
from collectors.gold_api import GoldAPICollector
from db import DatabaseManager


INVALID_POSITIVE_NUMBERS = [
    pytest.param(float("nan"), id="nan"),
    pytest.param(float("inf"), id="infinity"),
    pytest.param(True, id="boolean"),
]


def response_with(payload):
    response = MagicMock()
    response.__enter__.return_value = response
    response.read.return_value = json.dumps(payload).encode("utf-8")
    return response


def database_manager_with_failing_cursor(monkeypatch, error):
    pool = MagicMock()
    connection = MagicMock()
    cursor = MagicMock()
    cursor.execute.side_effect = error
    connection.cursor.return_value = cursor
    pool.get_connection.return_value = connection
    monkeypatch.setattr("db.ConnectionPool", MagicMock(return_value=pool))
    return DatabaseManager({}), cursor


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


@pytest.mark.parametrize("invalid_value", INVALID_POSITIVE_NUMBERS)
def test_gold_api_rejects_non_finite_or_boolean_price(
    monkeypatch,
    invalid_value,
):
    collector = GoldAPICollector(MagicMock())
    monkeypatch.setattr(
        "collectors.gold_api.urlopen",
        MagicMock(return_value=response_with({"price": invalid_value})),
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


@pytest.mark.parametrize("invalid_value", INVALID_POSITIVE_NUMBERS)
def test_exchange_rate_rejects_non_finite_or_boolean_rate(
    monkeypatch,
    invalid_value,
):
    manager = MagicMock()
    collector = ExchangeRateCollector(manager)
    monkeypatch.setattr(
        "collectors.exchange_rate.urlopen",
        MagicMock(
            return_value=response_with(
                {"result": "success", "rates": {"CNY": invalid_value}}
            )
        ),
    )

    with pytest.raises(CollectionError, match="exchange_rate"):
        collector.fetch()

    manager.upsert_exchange_rate.assert_not_called()


def test_exchange_rate_propagates_database_failure(monkeypatch):
    database_error = Error("db unavailable")
    manager, cursor = database_manager_with_failing_cursor(
        monkeypatch,
        database_error,
    )
    collector = ExchangeRateCollector(manager)
    monkeypatch.setattr(
        "collectors.exchange_rate.urlopen",
        MagicMock(
            return_value=response_with(
                {"result": "success", "rates": {"CNY": 7.25}}
            )
        ),
    )

    cache_sentinel = object()
    with _rate_cache["lock"]:
        previous_rate = _rate_cache["USD_CNY"]
        _rate_cache["USD_CNY"] = cache_sentinel
    try:
        with pytest.raises(Error) as exc_info:
            collector.fetch()

        assert exc_info.value is database_error
        assert cursor.execute.call_count == 1
        with _rate_cache["lock"]:
            assert _rate_cache["USD_CNY"] is cache_sentinel
    finally:
        with _rate_cache["lock"]:
            _rate_cache["USD_CNY"] = previous_rate


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


@pytest.mark.parametrize("invalid_value", INVALID_POSITIVE_NUMBERS)
def test_fawaz_rejects_non_finite_or_boolean_rates(
    monkeypatch,
    invalid_value,
):
    manager = MagicMock()
    collector = Fawazahmed0Collector(manager)
    monkeypatch.setattr(
        "collectors.fawazahmed0.urlopen",
        MagicMock(
            side_effect=[
                response_with(
                    {
                        "date": "2026-07-29",
                        "xau": {"cny": invalid_value, "usd": invalid_value},
                    }
                ),
                response_with(
                    {
                        "date": "2026-07-29",
                        "xag": {"cny": invalid_value, "usd": invalid_value},
                    }
                ),
            ]
        ),
    )

    with pytest.raises(CollectionError, match="fawazahmed0"):
        collector.fetch()

    manager.upsert_daily_ohlc.assert_not_called()


def test_fawaz_propagates_database_failure(monkeypatch):
    database_error = Error("db unavailable")
    manager, cursor = database_manager_with_failing_cursor(
        monkeypatch,
        database_error,
    )
    collector = Fawazahmed0Collector(manager)
    urlopen_mock = MagicMock(
        return_value=response_with(
            {"date": "2026-07-29", "xau": {"cny": 23000, "usd": 3200}}
        )
    )
    monkeypatch.setattr(
        "collectors.fawazahmed0.urlopen",
        urlopen_mock,
    )

    with pytest.raises(Error) as exc_info:
        collector.fetch()

    assert exc_info.value is database_error
    assert cursor.execute.call_count == 1
    assert urlopen_mock.call_count == 1
