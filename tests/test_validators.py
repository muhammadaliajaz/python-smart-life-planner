import pytest
from utils.validators import (
    validate_positive_number,
    validate_integer_range,
    validate_trip_duration,
    validate_travel_category,
    validate_destination_type,
    validate_email,
    validate_non_empty_string
)


class TestValidators:
    @pytest.mark.parametrize("val,expected_ok,expected_num", [
        (100, True, 100.0),
        ("2500.50", True, 2500.50),
        ("0.05", True, 0.05),
        (1, True, 1.0)
    ])
    def test_validate_positive_number_valid(self, val, expected_ok, expected_num):
        ok, num, err = validate_positive_number(val, "TestField")
        assert ok is True
        assert num == expected_num
        assert err == ""

    @pytest.mark.parametrize("val", [0, -10, "-50.0", "abc", None, "", " "])
    def test_validate_positive_number_invalid(self, val):
        ok, num, err = validate_positive_number(val, "TestField", min_val=0.01)
        assert ok is False
        assert num is None
        assert len(err) > 0

    @pytest.mark.parametrize("val,min_v,max_v,expected_int", [
        (1, 1, 10, 1),
        ("5", 1, 10, 5),
        (10.0, 1, 10, 10),
        ("50", 1, 100, 50)
    ])
    def test_validate_integer_range_valid(self, val, min_v, max_v, expected_int):
        ok, num, err = validate_integer_range(val, "TestInt", min_v, max_v)
        assert ok is True
        assert num == expected_int

    @pytest.mark.parametrize("val,min_v,max_v", [
        (0, 1, 10),
        (11, 1, 10),
        (-5, 0, 100),
        ("abc", 1, 10),
        (5.5, 1, 10),
        (None, 1, 10)
    ])
    def test_validate_integer_range_invalid(self, val, min_v, max_v):
        ok, num, err = validate_integer_range(val, "TestInt", min_v, max_v)
        assert ok is False
        assert num is None
        assert len(err) > 0

    def test_validate_trip_duration_valid(self):
        # 3 days, 2 nights
        ok, d, n, err = validate_trip_duration(3, 2)
        assert ok is True
        assert d == 3
        assert n == 2

        # Day trip: 1 day, 0 nights
        ok, d, n, err = validate_trip_duration(1, 0)
        assert ok is True
        assert d == 1
        assert n == 0

        # Equal days and nights: 5 days, 5 nights
        ok, d, n, err = validate_trip_duration(5, 5)
        assert ok is True
        assert d == 5
        assert n == 5

    def test_validate_trip_duration_invalid(self):
        # Nights > days
        ok, d, n, err = validate_trip_duration(2, 3)
        assert ok is False
        assert "cannot exceed" in err

        # Negative nights
        ok, d, n, err = validate_trip_duration(3, -1)
        assert ok is False

        # Zero days
        ok, d, n, err = validate_trip_duration(0, 0)
        assert ok is False

    @pytest.mark.parametrize("cat,expected", [
        ("budget", "Budget"),
        ("Standard", "Standard"),
        ("PREMIUM", "Premium")
    ])
    def test_validate_travel_category_valid(self, cat, expected):
        ok, result, err = validate_travel_category(cat)
        assert ok is True
        assert result == expected

    def test_validate_travel_category_invalid(self):
        ok, result, err = validate_travel_category("UltraLuxury")
        assert ok is False
        assert "Invalid category" in err

    @pytest.mark.parametrize("dest_type,expected", [
        ("mountains", "Mountains"),
        ("Historical Places", "Historical Places"),
        ("lakes & nature", "Lakes & Nature"),
        ("ANY", "Any"),
        ("", "Any")
    ])
    def test_validate_destination_type_valid(self, dest_type, expected):
        ok, result, err = validate_destination_type(dest_type)
        assert ok is True
        assert result == expected

    def test_validate_destination_type_invalid(self):
        ok, result, err = validate_destination_type("Beaches")
        assert ok is False

    @pytest.mark.parametrize("email,expected_ok", [
        ("developer@example.com", True),
        ("ali.khan@domain.pk", True),
        ("invalid-email", False),
        ("@missing-username.com", False),
        ("", False),
        (None, False)
    ])
    def test_validate_email(self, email, expected_ok):
        ok, err = validate_email(email)
        assert ok == expected_ok

    def test_validate_non_empty_string(self):
        ok, text, _ = validate_non_empty_string(" Islamabad ", "City")
        assert ok is True
        assert text == "Islamabad"

        ok, text, err = validate_non_empty_string("", "City")
        assert ok is False
