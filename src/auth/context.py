from __future__ import annotations

from typing import Optional

from flask import g


def set_auth(actor: str, role: str) -> None:
    g.auth_actor = actor
    g.auth_role = role


def get_actor() -> str:
    return getattr(g, "auth_actor", "anonymous")


def get_role() -> Optional[str]:
    return getattr(g, "auth_role", None)


def clear_auth() -> None:
    g.auth_actor = "anonymous"
    g.auth_role = None
