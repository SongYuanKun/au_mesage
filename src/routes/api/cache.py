"""API 层共享：时区与进程内 TTL 缓存。"""

import pytz
from cache import TtlCache

BEIJING_TZ = pytz.timezone("Asia/Shanghai")
api_ttl_cache = TtlCache()
