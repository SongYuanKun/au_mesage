"""管理端 API：数据源配置、审计查询。"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from api_errors import ApiError
from audit.service import log_audit
from auth.context import get_actor
from auth.decorators import require_role
from collectors import stats as collector_stats
from collectors.source_config import source_config_cache
from db import DatabaseManager


def register_admin_routes(bp: Blueprint, mysql_manager: DatabaseManager) -> None:
    @bp.route("/api/admin/sources", methods=["GET"])
    @require_role("admin", "ops")
    def list_sources():
        configs = mysql_manager.list_data_source_configs()
        if not configs:
            source_config_cache.refresh(force=True)
            configs = mysql_manager.list_data_source_configs() or source_config_cache.refresh(force=True)
        health = {row["source_id"]: row for row in collector_stats.snapshot()}
        merged = []
        for cfg in configs:
            sid = cfg["source_id"]
            merged.append({**cfg, "health": health.get(sid, {"source_id": sid})})
        return jsonify({"success": True, "data": merged})

    @bp.route("/api/admin/sources/<source_id>", methods=["PUT"])
    @require_role("admin")
    def update_source(source_id: str):
        body = request.get_json(silent=True) or {}
        if "enabled" not in body or "priority" not in body:
            raise ApiError.invalid_argument("需要 enabled 与 priority 字段")
        try:
            priority = int(body["priority"])
        except (TypeError, ValueError):
            raise ApiError.invalid_argument("priority 必须为整数")
        enabled = bool(body["enabled"])
        if priority < 0 or priority > 9999:
            raise ApiError.invalid_argument("priority 超出允许范围")

        result = mysql_manager.upsert_data_source_config(
            source_id,
            enabled=enabled,
            priority=priority,
            changed_by=get_actor(),
        )
        source_config_cache.invalidate()
        log_audit(
            action="admin.source.update",
            target=source_id,
            before_value=result.get("before"),
            after_value=result.get("after"),
        )
        return jsonify(
            {
                "success": True,
                "data": result.get("after"),
                "message": "配置已保存；采集器将在约 60 秒内按新配置生效",
            }
        )

    @bp.route("/api/admin/sources/<source_id>/rollback", methods=["POST"])
    @require_role("admin")
    def rollback_source(source_id: str):
        result = mysql_manager.rollback_data_source_config(source_id, changed_by=get_actor())
        if result is None:
            raise ApiError.not_found("无可回滚的历史版本")
        source_config_cache.invalidate()
        log_audit(
            action="admin.source.rollback",
            target=source_id,
            before_value=result.get("before"),
            after_value=result.get("after"),
        )
        return jsonify({"success": True, "data": result.get("after")})

    @bp.route("/api/admin/audit", methods=["GET"])
    @require_role("admin", "ops")
    def query_audit():
        start = request.args.get("start")
        end = request.args.get("end")
        action = request.args.get("action")
        limit_raw = request.args.get("limit", "100")
        try:
            limit = int(limit_raw)
        except (TypeError, ValueError):
            raise ApiError.invalid_argument("limit 必须为整数")
        if limit <= 0 or limit > 500:
            raise ApiError.invalid_argument("limit 须在 1–500 之间")

        rows = mysql_manager.query_audit_logs(start=start, end=end, action=action, limit=limit)
        return jsonify({"success": True, "data": rows})
