"""价差计算、汇率、健康检查。"""

from __future__ import annotations

import logging
from datetime import datetime

from flask import Blueprint, jsonify, request

from application.calculations import (
    build_history_comparison_response,
    build_purchase_calculate_response,
)
from application.exchange import (
    apply_usd_cny_cache_then_db,
    build_exchange_rate_success_payload,
)
from application.health import build_health_payload
from db import DatabaseManager

from .cache import BEIJING_TZ


def register_misc_routes(bp: Blueprint, mysql_manager: DatabaseManager) -> None:
    @bp.route("/api/history", methods=["POST"])
    def history():
        try:
            data = request.get_json()
            product_price = data.get("product_price")
            weight = data.get("weight")
            data_type = data.get("data_type")

            if not all([product_price, weight, data_type]):
                return jsonify({"error": "缺少参数: product_price, weight, 或 data_type"}), 400

            if (
                not isinstance(product_price, (int, float))
                or not isinstance(weight, (int, float))
                or weight <= 0
            ):
                return jsonify({"error": "product_price 和 weight 必须是有效数字，且 weight 必须大于0"}), 400

            market_price = mysql_manager.get_latest_market_price(data_type)

            if market_price is None:
                return jsonify({"error": f"无法获取 {data_type} 的最新市场价格"}), 404

            return jsonify(
                build_history_comparison_response(
                    float(product_price), float(weight), market_price
                )
            )

        except Exception as e:
            logging.error(f"计算价格差异接口错误: {e}")
            return jsonify({"error": "服务器内部错误"}), 500

    @bp.route("/api/calculate", methods=["POST"])
    def calculate_price_difference():
        """计算价格差异接口 - 使用 float 类型统一计算"""
        try:
            data = request.get_json()
            product_price = float(data.get("product_price"))
            weight = float(data.get("weight"))
            data_type = data.get("data_type")
            calculation_type = data.get("calculation_type", "purchase")  # noqa: F841

            if weight <= 0:
                return jsonify({"error": "weight 必须大于0"}), 400

            market_data = mysql_manager.get_latest_data(data_type)
            if not market_data:
                return jsonify({"error": f"未找到 {data_type} 的最新市场价格"}), 404

            market_price = float(market_data["recycle_price"])
            return jsonify(
                build_purchase_calculate_response(product_price, weight, market_price)
            )

        except (ValueError, TypeError):
            return jsonify({"error": "参数格式错误，请检查输入数据"}), 400
        except Exception as e:
            logging.error(f"计算价格差异接口错误: {e}")
            return jsonify({"error": "服务器内部错误"}), 500

    @bp.route("/api/exchange-rate", methods=["GET"])
    def api_exchange_rate():
        """返回最新汇率，优先用内存缓存，回退到数据库"""
        try:
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
                return jsonify({"success": False, "error": f"暂无 {base}/{target} 汇率数据"}), 404

            return jsonify(
                build_exchange_rate_success_payload(
                    base,
                    target,
                    rate,
                    datetime.now(BEIJING_TZ).isoformat(),
                )
            )
        except Exception as e:
            logging.error(f"汇率接口错误: {e}")
            return jsonify({"success": False, "error": "服务器内部错误"}), 500

    @bp.route("/api/health", methods=["GET"])
    def health_check():
        """服务健康检查接口"""
        return jsonify(build_health_payload(datetime.now(BEIJING_TZ).isoformat()))
