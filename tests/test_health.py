"""application.health 单元测试。"""

from application.health import build_health_payload


def test_build_health_payload():
    p = build_health_payload(
        "2025-03-22T12:00:00+08:00",
        database_ok=True,
        latest_updates=[{"latest_at": "2025-03-22T11:59:00+08:00"}],
    )
    assert p["status"] == "healthy"
    assert p["ready"] is True
    assert p["service"] == "price-data-api"
    assert p["timestamp"] == "2025-03-22T12:00:00+08:00"


def test_build_health_payload_is_unhealthy_when_data_is_stale_or_database_is_down():
    stale = build_health_payload(
        "2025-03-22T12:00:00+08:00", database_ok=True,
        latest_updates=[{"latest_at": "2025-03-22T11:30:00+08:00"}], max_data_age_seconds=600,
    )
    down = build_health_payload("2025-03-22T12:00:00+08:00", database_ok=False)
    assert stale["reason"] == "price_data_stale"
    assert down["reason"] == "database_unavailable"


def test_health_normalizes_timezones_and_rejects_far_future_data():
    healthy = build_health_payload(
        "2025-03-22T04:00:00Z", database_ok=True,
        latest_updates=[{"latest_at": "2025-03-22T12:00:00+08:00"}],
    )
    future = build_health_payload(
        "2025-03-22T04:00:00Z", database_ok=True,
        latest_updates=[{"latest_at": "2025-03-22T04:02:00Z"}], future_tolerance_seconds=60,
    )
    assert healthy["ready"] is True
    assert future["ready"] is False
    assert future["reason"] == "price_data_future"
