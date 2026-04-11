"""进程内缓存等基础设施（HTTP 层可复用）。"""

from .ttl_cache import TtlCache

__all__ = ["TtlCache"]
