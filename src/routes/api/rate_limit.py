from __future__ import annotations

import time

from api_errors import ApiError

from .cache import api_ttl_cache


def enforce_rate_limit(*, key: str, limit: int, window_seconds: int) -> None:
    now = time.time()
    cache_key = f"rl:{key}"
    bucket = api_ttl_cache.get(cache_key, ttl=window_seconds)
    if bucket is None:
        api_ttl_cache.set(cache_key, {"count": 1, "start": now})
        return

    start = float(bucket.get("start") or now)
    if now - start > window_seconds:
        api_ttl_cache.set(cache_key, {"count": 1, "start": now})
        return

    count = int(bucket.get("count") or 0) + 1
    if count > limit:
        raise ApiError.rate_limited("请求过于频繁，请稍后再试")
    bucket["count"] = count
    api_ttl_cache.set(cache_key, bucket)
