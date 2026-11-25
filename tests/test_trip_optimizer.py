import pytest
from models.destination import Destination
from models.trip import TripPlan
from services.trip_optimizer import TripOptimizer
from services.trip_calculator import TripCostCalculator


@pytest.fixture
def destinations_pool():
    return [
        Destination(
            name="Murree",
            region="Punjab",
            category="Mountains",
            room_capacity=2,
            base_transport_cost_per_person=2500,
            base_accommodation_cost_per_room_night=3500,
            food_cost_per_person_day=1500,
            activities_misc_cost_per_person=1500,
            category_rates={
                "Budget": {"transport_multiplier": 1.0, "accommodation_per_room_night": 2500, "food_multiplier": 1.0, "activities_multiplier": 0.8},
                "Standard": {"transport_multiplier": 1.4, "accommodation_per_room_night": 4500, "food_multiplier": 1.3, "activities_multiplier": 1.2},
                "Premium": {"transport_multiplier": 2.2, "accommodation_per_room_night": 9000, "food_multiplier": 2.0, "activities_multiplier": 2.0}
            }
        ),
        Destination(
            name="Hunza",
            region="Gilgit-Baltistan",
            category="Mountains",
            room_capacity=2,
            base_transport_cost_per_person=12000,
            base_accommodation_cost_per_room_night=6000,
            food_cost_per_person_day=2500,
            activities_misc_cost_per_person=3500,
            category_rates={
                "Budget": {"transport_multiplier": 1.0, "accommodation_per_room_night": 5000, "food_multiplier": 1.0, "activities_multiplier": 0.8},
                "Standard": {"transport_multiplier": 1.4, "accommodation_per_room_night": 8000, "food_multiplier": 1.3, "activities_multiplier": 1.2},
                "Premium": {"transport_multiplier": 2.2, "accommodation_per_room_night": 16000, "food_multiplier": 2.0, "activities_multiplier": 2.0}
            }
        ),
        Destination(
            name="Lahore",
            region="Punjab",
            category="Historical Places",
            room_capacity=2,
            base_transport_cost_per_person=2000,
            base_accommodation_cost_per_room_night=3000,
            food_cost_per_person_day=1800,
            activities_misc_cost_per_person=1200,
            category_rates={
                "Budget": {"transport_multiplier": 1.0, "accommodation_per_room_night": 2200, "food_multiplier": 1.0, "activities_multiplier": 0.8},
                "Standard": {"transport_multiplier": 1.3, "accommodation_per_room_night": 4000, "food_multiplier": 1.2, "activities_multiplier": 1.1},
                "Premium": {"transport_multiplier": 2.0, "accommodation_per_room_night": 8000, "food_multiplier": 1.8, "activities_multiplier": 1.8}
            }
        )
    ]


class TestTripOptimizer:
    def test_over_budget_generates_comprehensive_alternatives(self, destinations_pool):
        optimizer = TripOptimizer(destinations_pool)

        # Plan for Hunza: 4 travellers, 5 days, 4 nights, Standard => Costs ~150k+
        # Available Budget is 80,000 PKR => Over budget for Hunza
        # But Murree (71,280 in Budget) and Lahore (71,984 in Budget) fit within 80,000!
        plan = TripPlan(
            destination_name="Hunza",
            departure_city="Islamabad",
            travellers=4,
            days=5,
            nights=4,
            available_budget=80000.0,
            travel_category="Standard"
        )
        plan.breakdown = TripCostCalculator.calculate_cost(
            destinations_pool[1], 4, 5, 4, available_budget=80000.0, travel_category="Standard"
        )

        res = optimizer.generate_alternatives(plan, destinations_pool)
        assert "strategies" in res
        strats = res["strategies"]

        # 1. Increase budget strategy
        assert "increase_budget" in strats
        assert strats["increase_budget"]["additional_budget_needed"] == plan.breakdown.shortage

        # 2. Ranked alternatives must all be strictly <= available_budget
        ranked = res.get("ranked_alternatives", [])
        assert len(ranked) > 0
        for opt in ranked:
            assert opt["total_cost"] <= 80000.0
            assert opt["remaining_budget"] >= 0

        # Should suggest alternative destinations like Murree or Lahore that fit within 80k!
        dest_names = [opt["destination_name"] for opt in ranked]
        assert "Murree" in dest_names or "Lahore" in dest_names

    def test_reduction_strategies_when_feasible(self, destinations_pool):
        optimizer = TripOptimizer(destinations_pool)
        # Murree plan with 4 people, 3 days, 2 nights, Standard cost is ~60k
        # Budget is 35k (so 2 travellers or shorter duration fits)
        plan = TripPlan(
            destination_name="Murree",
            departure_city="Islamabad",
            travellers=4,
            days=3,
            nights=2,
            available_budget=35000.0,
            travel_category="Standard"
        )
        plan.breakdown = TripCostCalculator.calculate_cost(
            destinations_pool[0], 4, 3, 2, available_budget=35000.0, travel_category="Standard"
        )

        res = optimizer.generate_alternatives(plan, destinations_pool)
        strats = res["strategies"]

        assert strats["reduce_travellers"]["feasible"] is True
        assert strats["reduce_travellers"]["max_travellers"] < 4
        assert strats["reduce_travellers"]["cost"] <= 35000.0

        assert strats["reduce_duration"]["feasible"] is True
        assert strats["reduce_duration"]["cost"] <= 35000.0

    def test_extreme_budget_insufficient_for_any_destination(self, destinations_pool):
        optimizer = TripOptimizer(destinations_pool)
        # Budget 500 PKR is insufficient for any travel
        plan = TripPlan(
            destination_name="Murree",
            departure_city="Islamabad",
            travellers=4,
            days=3,
            nights=2,
            available_budget=500.0,
            travel_category="Standard"
        )
        plan.breakdown = TripCostCalculator.calculate_cost(
            destinations_pool[0], 4, 3, 2, available_budget=500.0, travel_category="Standard"
        )

        res = optimizer.generate_alternatives(plan, destinations_pool)
        # Never recommends unaffordable plans
        assert len(res["ranked_alternatives"]) == 0
        assert res["strategies"]["reduce_travellers"]["feasible"] is False
        assert res["strategies"]["reduce_duration"]["feasible"] is False
