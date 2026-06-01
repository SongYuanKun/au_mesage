"""认证辅助接口（会话确认与审计）。"""

from __future__ import annotations

from flask import Blueprint, jsonify

from auth.context import get_actor, get_role
from auth.decorators import optional_auth, require_role
from audit.service import log_audit


def register_auth_routes(bp: Blueprint) -> None:
    @bp.route("/api/auth/me", methods=["GET"])
    @require_role("admin", "ops", "user")
    def auth_me():
        return jsonify(
            {
                "success": True,
                "data": {"actor": get_actor(), "role": get_role()},
            }
        )

    @bp.route("/api/auth/session", methods=["POST"])
    @require_role("admin", "ops", "user")
    def auth_session():
        log_audit(action="auth.login", target="session", after_value={"role": get_role()})
        return jsonify({"success": True, "data": {"role": get_role()}})

    @bp.route("/api/auth/logout", methods=["POST"])
    @optional_auth()
    def auth_logout():
        if get_role():
            log_audit(action="auth.logout", target="session", actor=get_actor())
        return jsonify({"success": True})
