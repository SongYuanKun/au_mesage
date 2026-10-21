from __future__ import annotations

from functools import wraps
from typing import Callable, Optional

from flask import request

from api_errors import ApiError
from auth.config import actor_id_for_token, auth_enabled, resolve_role_from_bearer
from auth.context import clear_auth, get_actor, get_role, set_auth


def _parse_bearer() -> Optional[str]:
    header = request.headers.get("Authorization", "")
    if not header.lower().startswith("bearer "):
        return None
    return header[7:].strip() or None


def _request_token(*, allow_cookie: bool = False) -> Optional[str]:
    """优先使用显式 Bearer，SSE 使用登录校验后设置的 HttpOnly 同源 cookie。"""
    return _parse_bearer() or (request.cookies.get("au_session_token") if allow_cookie else None)


def authenticate_request(*, allow_cookie: bool = False, force_auth: bool = False) -> None:
    clear_auth()
    if not auth_enabled() and not force_auth:
        set_auth("anonymous", "guest")
        return

    token = _request_token(allow_cookie=allow_cookie)
    role = resolve_role_from_bearer(token)
    if role is None:
        raise ApiError.unauthorized("需要有效的 Bearer Token")
    set_auth(actor_id_for_token(token, role), role)


def require_role(*allowed: str, allow_cookie: bool = False, force_auth: bool = False) -> Callable:
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            authenticate_request(allow_cookie=allow_cookie, force_auth=force_auth)
            if not auth_enabled() and not force_auth:
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
                token = _request_token(allow_cookie=True)
                role = resolve_role_from_bearer(token)
                if role:
                    set_auth(actor_id_for_token(token, role), role)
                else:
                    set_auth("anonymous", None)
            else:
                set_auth("anonymous", "guest")
            return fn(*args, **kwargs)

        return wrapper

    return decorator
