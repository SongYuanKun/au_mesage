"""application 层纯函数测试。"""

from datetime import date

from application.price_responses import (
    build_gold_silver_ratio_payload,
    build_last_7_days_payload,
    build_price_overview_payload,
)
from application.trend_range import (
    parse_range_for_gold_silver_ratio,
    parse_range_for_price_trend_ohlc,
)


def test_build_price_overview_payload():
    rows = [
        {
            "data_type": "XAU",
            "recycle_price": 100.0,
            "real_time_price": 101.0,
            "yesterday_close": 99.0,
            "today_high": 102.0,
            "today_low": 98.0,
            "updated_at": "2025-01-01 12:00:00",
        }
    ]
    out = build_price_overview_payload(rows)
    assert out["success"] is True
    assert len(out["data"]) == 1
    d = out["data"][0]
    assert d["data_type"] == "XAU"
    assert d["change"] == 1.0
    assert d["change_pct"] is not None


def test_build_last_7_days_payload_missing_days():
    today = date(2025, 1, 10)
    rows = [{"date": "2025-01-10", "recycle_price": 500.0}]
    out = build_last_7_days_payload(rows, today)
    assert len(out["data"]) == 7
    assert out["data"][-1] == {"date": "2025-01-10", "recycle_price": 500.0}
    assert out["data"][0]["recycle_price"] is None


def test_parse_range_price_trend_invalid():
    start, err = parse_range_for_price_trend_ohlc("bad", date(2025, 1, 1))
    assert start is None
    assert "1d/7d" in (err or "")


def test_parse_range_gs_ratio_invalid():
    start, err = parse_range_for_gold_silver_ratio("bad", date(2025, 1, 1))
    assert start is None
    assert err == "无效的 range 参数"


def test_build_gold_silver_ratio_payload_stats():
    rows = [
        {"date": "2025-01-01", "ratio": 80.0, "gold_close": 1.0, "silver_close": 2.0},
        {"date": "2025-01-02", "ratio": 90.0, "gold_close": 1.0, "silver_close": 2.0},
    ]
    out = build_gold_silver_ratio_payload("7d", rows)
    assert out["stats"]["current"] == 90.0
    assert out["stats"]["min"] == 80.0
    assert out["stats"]["max"] == 90.0
