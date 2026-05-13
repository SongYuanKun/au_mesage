"""价差计算、汇率、健康检查。"""

from __future__ import annotations

import csv
import io
import json
from urllib.parse import quote
from datetime import datetime

from flask import Blueprint, Response, jsonify, request

from api_errors import ApiError

from application.calculations import (
    build_history_comparison_response,
    build_purchase_calculate_response,
)
from application.exchange import (
    apply_usd_cny_cache_then_db,
    build_exchange_rate_success_payload,
)
from application.health import build_health_payload
from application.metrics import build_quality_metrics_payload
from db import DatabaseManager

from .cache import BEIJING_TZ
from .rate_limit import enforce_rate_limit


def _first_forwarded_ip(v: str | None) -> str | None:
    if not v:
        return None
    parts = [p.strip() for p in v.split(",")]
    return parts[0] if parts and parts[0] else None


def register_misc_routes(bp: Blueprint, mysql_manager: DatabaseManager) -> None:
    @bp.route("/api/metrics/quality", methods=["GET"])
    def metrics_quality():
        now = datetime.now(BEIJING_TZ)
        latest = mysql_manager.get_latest_updates_by_group()
        counts = mysql_manager.get_counts_last_hour_by_group()
        return jsonify(build_quality_metrics_payload(latest, counts, now))

    @bp.route("/api/export/history", methods=["GET"])
    def export_history():
        data_type = request.args.get("data_type")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        fmt = (request.args.get("format") or "csv").lower()
        limit_raw = request.args.get("limit")

        if not data_type or not start_date or not end_date:
            raise ApiError.invalid_argument("缺少参数: data_type, start_date, 或 end_date")
        if fmt not in ("csv", "json"):
            raise ApiError.invalid_argument("format 仅支持 csv 或 json")

        limit = 5000
        if limit_raw is not None:
            try:
                limit = int(limit_raw)
            except (ValueError, TypeError):
                raise ApiError.invalid_argument("limit 必须为整数")
        if limit <= 0:
            raise ApiError.invalid_argument("limit 必须大于0")
        if limit > 20000:
            raise ApiError.invalid_argument("limit 不能超过 20000")

        ip = (
            _first_forwarded_ip(request.headers.get("X-Forwarded-For"))
            or request.remote_addr
            or "unknown"
        )
        enforce_rate_limit(key=f"export:{ip}", limit=10, window_seconds=600)

        rows = mysql_manager.query_data(start_date, end_date, data_type, limit)

        filename = f"{data_type}_{start_date}_to_{end_date}.{fmt}"
        cd = {
            "Content-Disposition": (
                f"attachment; filename=\"export.{fmt}\"; filename*=UTF-8''{quote(filename)}"
            )
        }
        if fmt == "json":
            body = json.dumps({"data": rows}, ensure_ascii=False, default=str)
            return Response(
                body,
                mimetype="application/json",
                headers=cd,
            )

        buf = io.StringIO()
        writer = csv.writer(buf)
        headers = [
            "trade_date",
            "trade_time",
            "data_type",
            "real_time_price",
            "recycle_price",
            "source",
            "currency",
            "created_at",
        ]
        writer.writerow(headers)
        for r in rows:
            writer.writerow([str(r.get(h, "")) for h in headers])
        return Response(
            buf.getvalue(),
            mimetype="text/csv",
            headers=cd,
        )

    @bp.route("/api/history", methods=["POST"])
    def history():
        data = request.get_json(silent=True) or {}
        product_price = data.get("product_price")
        weight = data.get("weight")
        data_type = data.get("data_type")

        if not all([product_price, weight, data_type]):
            raise ApiError.invalid_argument("缺少参数: product_price, weight, 或 data_type")

        try:
            product_price_f = float(product_price)
            weight_f = float(weight)
        except (ValueError, TypeError):
            raise ApiError.invalid_argument("product_price 和 weight 必须是有效数字")

        if weight_f <= 0:
            raise ApiError.invalid_argument("weight 必须大于0")

        market_price = mysql_manager.get_latest_market_price(data_type)
        if market_price is None:
            raise ApiError.not_found(f"无法获取 {data_type} 的最新市场价格")

        return jsonify(build_history_comparison_response(product_price_f, weight_f, market_price))

    @bp.route("/api/calculate", methods=["POST"])
    def calculate_price_difference():
        data = request.get_json(silent=True) or {}
        product_price = data.get("product_price")
        weight = data.get("weight")
        data_type = data.get("data_type")

        if product_price is None or weight is None or not data_type:
            raise ApiError.invalid_argument("缺少参数: product_price, weight, 或 data_type")

        try:
            product_price_f = float(product_price)
            weight_f = float(weight)
        except (ValueError, TypeError):
            raise ApiError.invalid_argument("参数格式错误，请检查输入数据")

        if weight_f <= 0:
            raise ApiError.invalid_argument("weight 必须大于0")

        market_data = mysql_manager.get_latest_data(data_type)
        if not market_data:
            raise ApiError.not_found(f"未找到 {data_type} 的最新市场价格")

        market_price = float(market_data["recycle_price"])
        return jsonify(build_purchase_calculate_response(product_price_f, weight_f, market_price))

    @bp.route("/api/exchange-rate", methods=["GET"])
    def api_exchange_rate():
        """返回最新汇率，优先用内存缓存，回退到数据库"""
        base = request.args.get("base", "USD").upper()
        target = request.args.get("target", "CNY").upper()

        cached_usd_cny = None
        try:
            from collectors.exchange_rate import get_usd_cny_rate

            if base == "USD" and target == "CNY":
                cached_usd_cny = get_usd_cny_rate()
        except ImportError:
            pass

        rate = apply_usd_cny_cache_then_db(
            base,
            target,
            cached_usd_cny,
            lambda: mysql_manager.get_latest_exchange_rate(base, target),
        )

        if rate is None:
            raise ApiError.not_found(f"暂无 {base}/{target} 汇率数据")

        return jsonify(
            build_exchange_rate_success_payload(
                base,
                target,
                rate,
                datetime.now(BEIJING_TZ).isoformat(),
            )
        )

    @bp.route("/api/health", methods=["GET"])
    def health_check():
        """服务健康检查接口"""
        return jsonify(build_health_payload(datetime.now(BEIJING_TZ).isoformat()))
