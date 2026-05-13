"""购买/历史场景下的每克价与大盘差异计算（无 Flask、无数据库）。"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict


def _to_decimal(v: Any) -> Decimal:
    if isinstance(v, Decimal):
        return v
    return Decimal(str(v))


def _round_decimal(v: Decimal, places: int) -> Decimal:
    q = Decimal("1").scaleb(-places)
    return v.quantize(q, rounding=ROUND_HALF_UP)


def build_history_comparison_response(
    product_price: float,
    weight: float,
    market_price: Any,
) -> Dict[str, Any]:
    """
    对应 POST /api/history 成功体（在已校验参数且 market_price 已解析之后）。
    market_price 类型与库返回一致，不做强制 float，以保持 JSON 序列化行为与原先一致。
    """
    if not weight:
        return {
            "price_per_gram": 0,
            "market_price": market_price or 0,
            "difference": 0,
            "difference_percentage": 0,
            "message": "",
        }

    try:
        pp = _to_decimal(product_price)
        w = _to_decimal(weight)
    except (InvalidOperation, ValueError, TypeError):
        pp = Decimal("0")
        w = Decimal("0")

    if w <= 0:
        return {
            "price_per_gram": 0,
            "market_price": market_price,
            "difference": 0,
            "difference_percentage": 0,
            "message": "",
        }

    price_per_gram = pp / w

    try:
        m_price = _to_decimal(market_price) if market_price is not None else Decimal("0")
    except (InvalidOperation, ValueError, TypeError):
        m_price = Decimal("0")

    difference = price_per_gram - m_price
    difference_percentage = (difference / m_price) * Decimal("100") if m_price > 0 else Decimal("0")

    diff_abs = abs(difference)
    msg = ""
    if m_price > 0:
        direction = "高" if difference > 0 else "低" if difference < 0 else "一致"
        msg = f"购买价比大盘{direction} {float(_round_decimal(diff_abs, 2)):.2f} 元/克 ({float(_round_decimal(abs(difference_percentage), 2)):.2f}%)"

    return {
        "price_per_gram": float(_round_decimal(price_per_gram, 4)),
        "market_price": market_price,
        "difference": float(_round_decimal(difference, 4)),
        "difference_percentage": float(_round_decimal(difference_percentage, 6)),
        "message": msg,
    }


def build_purchase_calculate_response(
    product_price: float,
    weight: float,
    market_price: float,
) -> Dict[str, Any]:
    """对应 POST /api/calculate 成功体（recycle_price 已转为 float）。"""
    if not weight:
        return {
            "price_per_gram": 0,
            "market_price": market_price,
            "total_difference": 0,
            "difference": 0,
            "difference_percentage": 0,
            "message_prefix": "购买价格差",
            "positive_message": "💡 比大盘价格贵",
            "negative_message": "💡 比大盘价格便宜",
            "message": "",
        }

    pp = _to_decimal(product_price)
    w = _to_decimal(weight)
    m_price = _to_decimal(market_price) if market_price is not None else Decimal("0")
    price_per_gram = pp / w
    difference = price_per_gram - m_price
    message_prefix = "购买价格差"
    positive_message = "💡 比大盘价格贵"
    negative_message = "💡 比大盘价格便宜"

    difference_percentage = (abs(difference) / m_price) * Decimal("100") if m_price > 0 else Decimal("0")

    if difference > 0:
        direction = "高"
    elif difference < 0:
        direction = "低"
    else:
        direction = "一致"
    msg = ""
    if m_price > 0:
        msg = f"购买价比大盘{direction} {float(_round_decimal(abs(difference), 2)):.2f} 元/克 ({float(_round_decimal(difference_percentage, 2)):.2f}%)"
    return {
        "price_per_gram": float(_round_decimal(price_per_gram, 4)),
        "market_price": float(_round_decimal(m_price, 4)),
        "total_difference": float(_round_decimal(difference * w, 4)),
        "difference": float(_round_decimal(difference, 4)),
        "difference_percentage": float(_round_decimal(difference_percentage, 2)),
        "message_prefix": message_prefix,
        "positive_message": positive_message,
        "negative_message": negative_message,
        "message": msg,
    }
