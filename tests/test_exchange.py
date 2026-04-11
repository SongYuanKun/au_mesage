"""application.exchange 单元测试。"""

from application.exchange import apply_usd_cny_cache_then_db, build_exchange_rate_success_payload


def test_usd_cny_cache_hit_never_calls_db():
    def boom():
        raise AssertionError("数据库不应在缓存命中时调用")

    r = apply_usd_cny_cache_then_db("USD", "CNY", 7.25, boom)
    assert r == 7.25


def test_usd_cny_cache_miss_uses_db():
    called = {"n": 0}

    def db():
        called["n"] += 1
        return 7.1

    r = apply_usd_cny_cache_then_db("USD", "CNY", None, db)
    assert r == 7.1
    assert called["n"] == 1


def test_non_usd_cny_only_uses_db():
    called = {"n": 0}

    def db():
        called["n"] += 1
        return 0.14

    r = apply_usd_cny_cache_then_db("EUR", "CNY", None, db)
    assert r == 0.14
    assert called["n"] == 1


def test_build_exchange_success_payload():
    p = build_exchange_rate_success_payload("USD", "CNY", 7.0, "2025-01-01T00:00:00+08:00")
    assert p["success"] is True
    assert p["rate"] == 7.0
