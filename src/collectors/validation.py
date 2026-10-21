"""Shared validation helpers for collector-supplied numeric values."""

import math


def parse_positive_finite(value: object) -> float:
    """Return a positive finite float, rejecting booleans and invalid values."""
    # bool is an int subclass, so float(True) would otherwise become 1.0.
    if isinstance(value, bool):
        raise ValueError("boolean is not a valid numeric value")

    parsed = float(value)
    if not math.isfinite(parsed) or parsed <= 0:
        raise ValueError("value must be positive and finite")
    return parsed
