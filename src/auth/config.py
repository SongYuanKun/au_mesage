"""认证配置：Bearer Token 映射角色（最小闭环，可选启用）。"""

from __future__ import annotations

import os
import secrets
import hashlib
from typing import Optional


def auth_enabled() -> bool:
    return os.environ.get("AUTH_ENABLED", "false").lower() in ("1", "true", "yes")


def _token_role_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    pairs = (
        ("AUTH_ADMIN_TOKEN", "admin"),
        ("AUTH_OPS_TOKEN", "ops"),
        ("AUTH_USER_TOKEN", "user"),
    )
    for env_key, role in pairs:
        token = os.environ.get(env_key, "").strip()
        if token:
            mapping[token] = role
    legacy = os.environ.get("ADMIN_API_TOKEN", "").strip()
    if legacy and legacy not in mapping:
        mapping[legacy] = "admin"
    return mapping


def resolve_role_from_bearer(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    return _token_role_map().get(token)


def actor_id_for_token(token: str, role: str) -> str:
    """稳定的限流/审计主体标识，不保留原始 Bearer Token。"""
    token_hash = hashlib.blake2b(token.encode("utf-8"), digest_size=8).hexdigest()
    return f"token:{role}:{token_hash}"


def constant_time_equal(a: str, b: str) -> bool:
    return secrets.compare_digest(a.encode("utf-8"), b.encode("utf-8"))
