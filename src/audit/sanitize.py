from __future__ import annotations

import re
from typing import Any

_SENSITIVE_KEYS = frozenset(
    {
        "token",
        "password",
        "secret",
        "webhook",
        "authorization",
        "smtp_pass",
        "telegram_bot_token",
        "wechat_webhook_url",
    }
)

_REDACT = "[REDACTED]"


def _key_is_sensitive(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in _SENSITIVE_KEYS)


def sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _REDACT if _key_is_sensitive(str(k)) else sanitize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_value(v) for v in value]
    if isinstance(value, str):
        if re.search(r"(https?://)?[\w-]*webhook", value, re.I):
            return _REDACT
        if len(value) > 48 and re.fullmatch(r"[A-Za-z0-9._-]+", value):
            return _REDACT
    return value
