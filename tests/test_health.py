"""application.health 单元测试。"""

from application.health import build_health_payload


def test_build_health_payload():
    p = build_health_payload("2025-03-22T12:00:00+08:00")
    assert p["status"] == "healthy"
    assert p["service"] == "price-data-api"
    assert p["timestamp"] == "2025-03-22T12:00:00+08:00"
