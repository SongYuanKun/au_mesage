"""价格、趋势、历史类 API。"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

import pytz

from flask import Blueprint, jsonify, request

from api_errors import ApiError

from application.price_responses import (
    build_gold_silver_ratio_payload,
    build_last_7_days_payload,
    build_price_overview_payload,
    build_price_trend_candlestick_response,
    build_price_trend_line_response,
    intraday_rows_to_line_series,
    ohlc_rows_to_candlestick_series,
)
from application.trend_range import (
    parse_range_for_gold_silver_ratio,
    parse_range_for_price_trend_ohlc,
)
from db import DatabaseManager

from .cache import BEIJING_TZ, api_ttl_cache


def register_price_routes(bp: Blueprint, mysql_manager: DatabaseManager) -> None:
    @bp.route("/api/price-overview", methods=["GET"])
    def price_overview():
        """返回金/银的综合概览：当前价、涨跌、今日高低（单条SQL + 10s缓存）"""
        cached = api_ttl_cache.get("price_overview", ttl=10)
        if cached is not None:
            return jsonify(cached)
        today = datetime.now(BEIJING_TZ).date()
        yesterday = today - timedelta(days=1)
        today_str = today.strftime("%Y-%m-%d")
        yesterday_str = yesterday.strftime("%Y-%m-%d")

        rows = mysql_manager.get_price_overview_data(today_str, yesterday_str)
        if not rows:
            rows = mysql_manager.get_price_overview_data_fallback()
        resp = build_price_overview_payload(rows, now=datetime.now(BEIJING_TZ))
        api_ttl_cache.set("price_overview", resp)
        return jsonify(resp)

    @bp.route("/api/latest-price", methods=["GET"])
    def get_latest_price():
        """获取最新价格接口"""
        data_type = request.args.get("data_type")
        if not data_type:
            data = mysql_manager.get_latest_data_by_type()
            if data:
                return jsonify({"success": True, "data": data})
            raise ApiError.not_found("未找到任何数据")

        data = mysql_manager.get_latest_data(data_type)
        if data:
            return jsonify({"success": True, "data": data})
        raise ApiError.not_found(f"未找到 {data_type} 的最新数据")

    @bp.route("/api/recent-history", methods=["GET"])
    def get_recent_price_history():
        """获取指定data_type的近期历史价格数据接口 (用于图表)"""
        data_type = request.args.get("data_type")
        if not data_type:
            raise ApiError.invalid_argument("缺少 data_type 参数")

        history_data = mysql_manager.get_price_history(data_type, limit=30)

        if history_data:
            return jsonify({"success": True, "data": history_data})
        raise ApiError.not_found(f"未找到 {data_type} 的近期历史数据")

    @bp.route("/api/daily-history", methods=["GET"])
    def get_daily_history():
        """获取指定日期和data_type的所有历史数据接口。默认返回今天的所有数据。"""
        date_str = request.args.get("date", datetime.now(BEIJING_TZ).strftime("%Y-%m-%d"))

        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            raise ApiError.invalid_argument("日期格式错误，应为 YYYY-MM-DD")

        data_type = request.args.get("data_type")

        history_data = mysql_manager.get_daily_history(date_str, data_type)

        if history_data:
            return jsonify(
                {
                    "success": True,
                    "date": date_str,
                    "data_type": data_type,
                    "data": history_data,
                }
            )
        raise ApiError.not_found(f"未找到 {date_str} 的历史数据")

    @bp.route("/api/last-1-hour", methods=["GET"])
    def api_last_1_hour():
        """返回指定 data_type 的近 1 小时内的所有数据"""
        data_type = request.args.get("data_type")
        if not data_type:
            raise ApiError.invalid_argument("缺少 data_type 参数")

        history_data = mysql_manager.get_price_history_last_hour(data_type)

        return jsonify({"success": True, "data": history_data or []})

    @bp.route("/api/last-7-days", methods=["GET"])
    def api_last_7_days():
        """返回指定 data_type 的近 7 天每日回收价格（单条SQL + 60s缓存）"""
        data_type = request.args.get("data_type")
        if not data_type:
            raise ApiError.invalid_argument("缺少 data_type 参数")

        cache_key = f"last7_{data_type}"
        cached = api_ttl_cache.get(cache_key, ttl=60)
        if cached is not None:
            return jsonify(cached)

        today = datetime.now(BEIJING_TZ).date()
        start_date = (today - timedelta(days=6)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")

        rows = mysql_manager.get_last_n_days_daily_price(data_type, start_date, end_date)
        resp = build_last_7_days_payload(rows, today)
        api_ttl_cache.set(cache_key, resp)
        return jsonify(resp)

    @bp.route("/api/price-trend", methods=["GET"])
    def api_price_trend():
        """
        返回价格趋势数据，支持多时间维度。
        range: 1d / 7d / 30d / 90d / 1y / all
        1d 返回分钟级日内数据，其余返回日K线OHLC数据。
        """
        data_type = request.args.get("data_type")
        range_str = request.args.get("range", "7d")
        if not data_type:
            raise ApiError.invalid_argument("缺少 data_type 参数")

        today = datetime.now(BEIJING_TZ).date()

        if range_str == "1d":
            cache_key = f"trend_1d_{data_type}"
            cached = api_ttl_cache.get(cache_key, ttl=30)
            if cached is not None:
                return jsonify(cached)
            rows = mysql_manager.get_intraday_trend(data_type, today.strftime("%Y-%m-%d"))
            data = intraday_rows_to_line_series(rows)
            resp = build_price_trend_line_response(data)
            api_ttl_cache.set(cache_key, resp)
            return jsonify(resp)

        start_date, err = parse_range_for_price_trend_ohlc(range_str, today)
        if err:
            raise ApiError.invalid_argument(err)

        cache_key = f"trend_{range_str}_{data_type}"
        ttl = 60 if range_str in ("7d", "30d") else 300
        cached = api_ttl_cache.get(cache_key, ttl=ttl)
        if cached is not None:
            return jsonify(cached)

        end_date = today.strftime("%Y-%m-%d")
        rows = mysql_manager.get_ohlc_trend(data_type, start_date, end_date)
        data = ohlc_rows_to_candlestick_series(rows)
        resp = build_price_trend_candlestick_response(range_str, data)
        api_ttl_cache.set(cache_key, resp)
        return jsonify(resp)

    @bp.route("/api/gold-silver-ratio", methods=["GET"])
    def api_gold_silver_ratio():
        """返回金银比走势数据"""
        range_str = request.args.get("range", "30d")
        today = datetime.now(BEIJING_TZ).date()

        start_date, err = parse_range_for_gold_silver_ratio(range_str, today)
        if err:
            raise ApiError.invalid_argument(err)

        cache_key = f"gs_ratio_{range_str}"
        ttl = 60 if range_str in ("7d", "30d") else 300
        cached = api_ttl_cache.get(cache_key, ttl=ttl)
        if cached is not None:
            return jsonify(cached)

        end_date = today.strftime("%Y-%m-%d")
        rows = mysql_manager.get_gold_silver_ratio(start_date, end_date)
        resp = build_gold_silver_ratio_payload(range_str, rows)
        api_ttl_cache.set(cache_key, resp)
        return jsonify(resp)
