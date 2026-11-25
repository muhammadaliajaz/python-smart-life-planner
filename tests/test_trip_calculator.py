import pytest
from models.destination import Destination
from services.trip_calculator import TripCostCalculator
from utils.calculations import calculate_rooms_needed


@pytest.fixture
def sample_destination():
    return Destination(
        name="Murree",
        region="Punjab",
        category="Mountains",
        room_capacity=2,
        base_transport_cost_per_person=3000.0,
        base_accommodation_cost_per_room_night=4000.0,
        food_cost_per_person_day=2000.0,
        activities_misc_cost_per_person=2000.0,
        category_rates={
            "Budget": {
                "transport_multiplier": 1.0,
                "accommodation_per_room_night": 3000.0,
                "food_multiplier": 1.0,
                "activities_multiplier": 0.8
            },
            "Standard": {
                "transport_multiplier": 1.4,
                "accommodation_per_room_night": 5000.0,
                "food_multiplier": 1.3,
                "activities_multiplier": 1.2
            },
            "Premium": {
                "transport_multiplier": 2.2,
                "accommodation_per_room_night": 10000.0,
                "food_multiplier": 2.0,
                "activities_multiplier": 2.0
            }
        }
    )


class TestTripCalculator:
    def test_room_calculation(self):
        # 1 traveller, room capacity 2 => 1 room
        assert calculate_rooms_needed(1, 2) == 1
        # 2 travellers, room capacity 2 => 1 room
        assert calculate_rooms_needed(2, 2) == 1
        # 3 travellers, room capacity 2 => 2 rooms (ceiling division)
        assert calculate_rooms_needed(3, 2) == 2
        # 5 travellers, room capacity 2 => 3 rooms
        assert calculate_rooms_needed(5, 2) == 3

    def test_zero_night_trip_has_zero_accommodation(self, sample_destination):
        bk = TripCostCalculator.calculate_cost(
            destination=sample_destination,
            travellers=2,
            days=1,
            nights=0,
            available_budget=50000,
            travel_category="Standard",
            emergency_percentage=10.0
        )
        assert bk.accommodation == 0.0
        assert bk.total_cost > 0
        assert bk.remaining_budget == 50000 - bk.total_cost

    def test_cost_components_accuracy(self, sample_destination):
        # Standard category rates:
        # transport = 3000 * 1.4 = 4200 per person
        # accom = 5000 per room/night
        # food = 2000 * 1.3 = 2600 per person/day
        # act = 2000 * 1.2 = 2400 per person
        # For 2 travellers, 3 days, 2 nights:
        # rooms = ceil(2/2) = 1 room
        # transport = 4200 * 2 = 8400
        # accom = 5000 * 1 * 2 = 10000
        # food = 2600 * 2 * 3 = 15600
        # act = 2400 * 2 = 4800
        # subtotal = 8400 + 10000 + 15600 + 4800 = 38800
        # emergency (10%) = 3880
        # total = 38800 + 3880 = 42680
        bk = TripCostCalculator.calculate_cost(
            destination=sample_destination,
            travellers=2,
            days=3,
            nights=2,
            available_budget=50000,
            travel_category="Standard",
            emergency_percentage=10.0
        )
        assert bk.transportation == 8400.0
        assert bk.accommodation == 10000.0
        assert bk.food == 15600.0
        assert bk.activities_misc == 4800.0
        assert bk.subtotal == 38800.0
        assert bk.emergency_allowance == 3880.0
        assert bk.total_cost == 42680.0
        assert bk.cost_per_person == 21340.0
        assert bk.required_rooms == 1
        assert bk.feasibility_status == "Within Budget"
        assert bk.remaining_budget == 50000 - 42680

    def test_budget_boundaries(self, sample_destination):
        # Exact cost = 42680.0
        cost = 42680.0

        # Exact budget boundary
        bk_exact = TripCostCalculator.calculate_cost(
            sample_destination, 2, 3, 2, available_budget=cost, travel_category="Standard"
        )
        assert bk_exact.feasibility_status == "Exactly Within Budget"
        assert bk_exact.remaining_budget == 0.0
        assert bk_exact.shortage == 0.0

        # PKR 1 above boundary
        bk_above = TripCostCalculator.calculate_cost(
            sample_destination, 2, 3, 2, available_budget=cost + 1, travel_category="Standard"
        )
        assert bk_above.feasibility_status == "Within Budget"
        assert bk_above.remaining_budget == 1.0
        assert bk_above.shortage == 0.0

        # PKR 1 below boundary
        bk_below = TripCostCalculator.calculate_cost(
            sample_destination, 2, 3, 2, available_budget=cost - 1, travel_category="Standard"
        )
        assert bk_below.feasibility_status == "Over Budget"
        assert bk_below.shortage == 1.0
        assert bk_below.remaining_budget == 0.0

    def test_invalid_parameters_raise_value_error(self, sample_destination):
        with pytest.raises(ValueError):
            TripCostCalculator.calculate_cost(sample_destination, travellers=0, days=2, nights=1, available_budget=10000)

        with pytest.raises(ValueError):
            TripCostCalculator.calculate_cost(sample_destination, travellers=2, days=0, nights=1, available_budget=10000)

        with pytest.raises(ValueError):
            TripCostCalculator.calculate_cost(sample_destination, travellers=2, days=2, nights=3, available_budget=10000)

        with pytest.raises(ValueError):
            TripCostCalculator.calculate_cost(sample_destination, travellers=2, days=2, nights=1, available_budget=-10)
