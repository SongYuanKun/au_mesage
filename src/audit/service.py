from __future__ import annotations

import json
import logging
from typing import Any, Optional

from flask import has_request_context, request

from audit.sanitize import sanitize_value
from auth.context import get_actor

_audit_writer: Optional[Any] = None

logger = logging.getLogger(__name__)


def bind_audit_writer(writer: Any) -> None:
    global _audit_writer
    _audit_writer = writer


def _request_meta() -> tuple[Optional[str], Optional[str]]:
    if not has_request_context():
        return None, None
    ip = request.headers.get("X-Forwarded-For") or request.remote_addr
    if ip and "," in ip:
        ip = ip.split(",")[0].strip()
    return ip, (request.headers.get("User-Agent") or "")[:512] or None


def log_audit(
    *,
    action: str,
    target: Optional[str] = None,
    before_value: Any = None,
    after_value: Any = None,
    actor: Optional[str] = None,
) -> None:
    actor = actor or get_actor()
    before_json = json.dumps(sanitize_value(before_value), ensure_ascii=False) if before_value is not None else None
    after_json = json.dumps(sanitize_value(after_value), ensure_ascii=False) if after_value is not None else None
    ip, user_agent = _request_meta()

    if _audit_writer is None:
        logger.info(
            "audit action=%s actor=%s target=%s",
            action,
            actor,
            target,
        )
        return

    try:
        _audit_writer.insert_audit_log(
            actor=actor,
            action=action,
            target=target,
            before_value=before_json,
            after_value=after_json,
            ip=ip,
            user_agent=user_agent,
        )
    except Exception:
        logger.exception("写入审计日志失败 action=%s", action)
