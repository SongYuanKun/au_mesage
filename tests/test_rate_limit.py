import pytest

from api_errors import ApiError
from routes.api.cache import api_ttl_cache
from routes.api.rate_limit import enforce_rate_limit


def test_rate_limit_blocks_after_limit(monkeypatch):
    api_ttl_cache.clear()
    t = 1000.0

    def now():
        return t

    monkeypatch.setattr("routes.api.rate_limit.time.time", now)

    for _ in range(3):
        enforce_rate_limit(key="k", limit=3, window_seconds=60)

    with pytest.raises(ApiError) as e:
        enforce_rate_limit(key="k", limit=3, window_seconds=60)
    assert e.value.code == "RATE_LIMITED"


def test_rate_limit_resets_after_window(monkeypatch):
    api_ttl_cache.clear()
    t = 2000.0

    def now():
        return t

    monkeypatch.setattr("routes.api.rate_limit.time.time", now)

    for _ in range(2):
        enforce_rate_limit(key="k2", limit=2, window_seconds=10)

    t += 11
    enforce_rate_limit(key="k2", limit=2, window_seconds=10)

