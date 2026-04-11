"""application.calculations 单元测试。"""

from application.calculations import (
    build_history_comparison_response,
    build_purchase_calculate_response,
)


def test_history_comparison():
    out = build_history_comparison_response(1000.0, 10.0, 95.0)
    assert out["price_per_gram"] == 100.0
    assert out["market_price"] == 95.0
    assert out["difference"] == 5.0
    assert abs(out["difference_percentage"] - (5.0 / 95.0 * 100)) < 1e-9


def test_history_comparison_zero_market():
    out = build_history_comparison_response(100.0, 10.0, 0)
    assert out["difference_percentage"] == 0


def test_purchase_calculate_rounding():
    out = build_purchase_calculate_response(1000.0, 3.0, 300.0)
    assert out["price_per_gram"] == round(1000.0 / 3.0, 4)
    assert out["market_price"] == 300.0
    assert out["difference_percentage"] == round((abs(1000.0 / 3.0 - 300) / 300) * 100, 2)
