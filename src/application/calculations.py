"""购买/历史场景下的每克价与大盘差异计算（无 Flask、无数据库）。"""

from __future__ import annotations

from typing import Any, Dict


def build_history_comparison_response(
    product_price: float,
    weight: float,
    market_price: Any,
) -> Dict[str, Any]:
    """
    对应 POST /api/history 成功体（在已校验参数且 market_price 已解析之后）。
    market_price 类型与库返回一致，不做强制 float，以保持 JSON 序列化行为与原先一致。
    """
    price_per_gram = product_price / weight
    difference = price_per_gram - market_price
    difference_percentage = (difference / market_price) * 100 if market_price != 0 else 0
    return {
        "price_per_gram": price_per_gram,
        "market_price": market_price,
        "difference": difference,
        "difference_percentage": difference_percentage,
    }


def build_purchase_calculate_response(
    product_price: float,
    weight: float,
    market_price: float,
) -> Dict[str, Any]:
    """对应 POST /api/calculate 成功体（recycle_price 已转为 float）。"""
    price_per_gram = product_price / weight
    difference = price_per_gram - market_price
    message_prefix = "购买价格差"
    positive_message = "💡 比大盘价格贵"
    negative_message = "💡 比大盘价格便宜"
    difference_percentage = (abs(difference) / market_price) * 100 if market_price != 0 else 0
    return {
        "price_per_gram": round(price_per_gram, 4),
        "market_price": round(market_price, 4),
        "total_difference": round(difference * weight, 4),
        "difference": round(difference, 4),
        "difference_percentage": round(difference_percentage, 2),
        "message_prefix": message_prefix,
        "positive_message": positive_message,
        "negative_message": negative_message,
    }
