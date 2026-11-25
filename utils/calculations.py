import math
from typing import Union


def calculate_rooms_needed(travellers: int, room_capacity: int = 2) -> int:
    """
    Calculate required rooms using ceiling division.
    Required rooms = ceiling(travellers / room_capacity).
    """
    if travellers <= 0:
        return 0
    cap = max(1, room_capacity)
    return math.ceil(travellers / cap)


def format_pkr(amount: Union[int, float]) -> str:
    """
    Format monetary amounts nicely in PKR with comma separators.
    Example: 25000 -> PKR 25,000.00
    """
    try:
        val = float(amount)
        return f"PKR {val:,.2f}"
    except (ValueError, TypeError):
        return f"PKR 0.00"


def calculate_percentage(part: Union[int, float], whole: Union[int, float]) -> float:
    """Safely calculate percentage (part / whole * 100)."""
    if whole is None or whole == 0:
        return 0.0
    return round((float(part) / float(whole)) * 100, 2)


def safe_divide(numerator: Union[int, float], denominator: Union[int, float], default: float = 0.0) -> float:
    """Safely perform division avoiding ZeroDivisionError."""
    if denominator == 0 or denominator is None:
        return default
    return float(numerator) / float(denominator)
