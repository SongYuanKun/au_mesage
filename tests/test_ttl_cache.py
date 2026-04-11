"""TtlCache 单元测试（与 route 层解耦，可独立验证缓存语义）。"""

from unittest.mock import patch

from cache.ttl_cache import TtlCache


def test_get_missing_returns_none():
    c = TtlCache()
    assert c.get("any", ttl=10) is None


def test_set_then_get_within_ttl():
    c = TtlCache()
    c.set("k", {"x": 1})
    assert c.get("k", ttl=60) == {"x": 1}


def test_clear_removes_all():
    c = TtlCache()
    c.set("a", 1)
    c.clear()
    assert c.get("a", ttl=60) is None


def test_expires_after_ttl_seconds():
    c = TtlCache()
    with patch("cache.ttl_cache.time") as mock_time:
        # set 调用一次 time.time；两次 get 各调用一次
        mock_time.time.side_effect = [1_000_000.0, 1_000_005.0, 1_000_010.0]
        c.set("k", "v")
        assert c.get("k", ttl=10) == "v"
        assert c.get("k", ttl=10) is None
