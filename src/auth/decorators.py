from __future__ import annotations

from functools import wraps
from typing import Callable, Optional

from flask import request

from api_errors import ApiError
from auth.config import auth_enabled, resolve_role_from_bearer
from auth.context import clear_auth, get_actor, get_role, set_auth


def _parse_bearer() -> Optional[str]:
    header = request.headers.get("Authorization", "")
    if not header.lower().startswith("bearer "):
        return None
    return header[7:].strip() or None


def authenticate_request() -> None:
    clear_auth()
    if not auth_enabled():
        set_auth("anonymous", "guest")
        return

    token = _parse_bearer()
    role = resolve_role_from_bearer(token)
    if role is None:
        raise ApiError.unauthorized("需要有效的 Bearer Token")
    set_auth(f"token:{role}", role)


def require_role(*allowed: str) -> Callable:
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            authenticate_request()
            if not auth_enabled():
                return fn(*args, **kwargs)

            role = get_role()
            if role not in allowed:
                from audit.service import log_audit

                log_audit(
                    action="auth.forbidden",
                    target=request.path,
                    before_value={"required_roles": list(allowed)},
                    after_value={"role": role},
                    actor=get_actor(),
                )
                raise ApiError.forbidden("无权限访问该资源")
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def optional_auth() -> Callable:
    """解析身份但不强制；用于审计记录操作者。"""

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            clear_auth()
            if auth_enabled():
                token = _parse_bearer()
                role = resolve_role_from_bearer(token)
                if role:
                    set_auth(f"token:{role}", role)
                else:
                    set_auth("anonymous", None)
            else:
                set_auth("anonymous", "guest")
            return fn(*args, **kwargs)

        return wrapper

    return decorator
