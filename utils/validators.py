import re
from collections import namedtuple
from typing import Any, Tuple, Optional

ValidationResult = namedtuple("ValidationResult", ["is_valid", "error_message", "value"])

MAX_TRAVELLERS = 100
MAX_TRIP_DAYS = 60
MIN_BUDGET = 100.0

VALID_CATEGORIES = ("Budget", "Standard", "Premium")
VALID_DESTINATION_TYPES = ("Mountains", "Historical Places", "Lakes & Nature", "Any")


def validate_positive_number(val: Any, field_name: str = "Amount", min_val: float = 0.01) -> Tuple[bool, Optional[float], str]:
    """Validate that value is a positive number."""
    if val is None:
        return False, None, f"{field_name} cannot be empty."
    try:
        num = float(val)
    except (ValueError, TypeError):
        return False, None, f"{field_name} must be a valid number."
    
    if num < min_val:
        return False, None, f"{field_name} must be at least {min_val:,.2f}."
    return True, num, ""


def validate_integer_range(val: Any, field_name: str, min_val: int = 1, max_val: int = 100) -> Tuple[bool, Optional[int], str]:
    """Validate that value is an integer within [min_val, max_val]."""
    if val is None or str(val).strip() == "":
        return False, None, f"{field_name} cannot be empty."
    try:
        # Check if float before int
        float_val = float(val)
        if not float_val.is_integer():
            return False, None, f"{field_name} must be a whole integer."
        num = int(float_val)
    except (ValueError, TypeError):
        return False, None, f"{field_name} must be a valid integer."

    if num < min_val or num > max_val:
        return False, None, f"{field_name} must be between {min_val} and {max_val}."
    return True, num, ""


def validate_trip_duration(days_val: Any, nights_val: Any) -> Tuple[bool, Optional[int], Optional[int], str]:
    """
    Validate days and nights.
    Days must be >= 1 and <= MAX_TRIP_DAYS.
    Nights must be >= 0 and <= days.
    """
    ok_days, days, err_days = validate_integer_range(days_val, "Trip days", 1, MAX_TRIP_DAYS)
    if not ok_days:
        return False, None, None, err_days

    ok_nights, nights, err_nights = validate_integer_range(nights_val, "Trip nights", 0, MAX_TRIP_DAYS)
    if not ok_nights:
        return False, None, None, err_nights

    if nights > days:
        return False, None, None, f"Trip nights ({nights}) cannot exceed trip days ({days})."

    return True, days, nights, ""


def validate_travel_category(category: str) -> Tuple[bool, str, str]:
    """Validate travel category."""
    if not category:
        return False, "", "Travel category cannot be empty."
    cat_clean = category.strip().capitalize()
    if cat_clean not in VALID_CATEGORIES:
        return False, "", f"Invalid category '{category}'. Must be one of: {', '.join(VALID_CATEGORIES)}."
    return True, cat_clean, ""


def validate_destination_type(dest_type: str) -> Tuple[bool, str, str]:
    """Validate destination preference type."""
    if not dest_type:
        return True, "Any", ""
    dest_clean = dest_type.strip()
    # Normalize match
    for valid in VALID_DESTINATION_TYPES:
        if dest_clean.lower() == valid.lower():
            return True, valid, ""
    return False, "", f"Invalid destination type '{dest_type}'. Options: {', '.join(VALID_DESTINATION_TYPES)}."


def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email address format."""
    if not email or not isinstance(email, str):
        return False, "Email address cannot be empty."
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(pattern, email.strip()):
        return False, f"Invalid email format: '{email}'."
    return True, ""


def validate_non_empty_string(val: Any, field_name: str = "Input", min_len: int = 1, max_len: int = 100) -> Tuple[bool, str, str]:
    """Validate non-empty string with length bounds."""
    if val is None:
        return False, "", f"{field_name} cannot be empty."
    text = str(val).strip()
    if len(text) < min_len:
        return False, "", f"{field_name} must contain at least {min_len} character(s)."
    if len(text) > max_len:
        return False, "", f"{field_name} cannot exceed {max_len} characters."
    return True, text, ""
