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
