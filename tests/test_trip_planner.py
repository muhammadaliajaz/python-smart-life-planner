import pytest
import os
from services.trip_planner import TripPlanner
from utils.data_manager import DataManager


@pytest.fixture
def planner(tmp_path):
    dm = DataManager(base_dir=str(tmp_path))
    # Write a sample destinations.json into tmp_path/data
    import json
    dest_path = os.path.join(str(tmp_path), "data", "destinations.json")
    sample_data = {
        "destinations": [
            {
                "name": "Murree",
                "region": "Punjab",
                "category": "Mountains",
                "room_capacity": 2,
                "base_transport_cost_per_person": 3000,
                "base_accommodation_cost_per_room_night": 4000,
                "food_cost_per_person_day": 2000,
                "activities_misc_cost_per_person": 2000,
                "category_rates": {
                    "Budget": {"transport_multiplier": 1.0, "accommodation_per_room_night": 3000, "food_multiplier": 1.0, "activities_multiplier": 0.8},
                    "Standard": {"transport_multiplier": 1.4, "accommodation_per_room_night": 5000, "food_multiplier": 1.3, "activities_multiplier": 1.2},
                    "Premium": {"transport_multiplier": 2.2, "accommodation_per_room_night": 10000, "food_multiplier": 2.0, "activities_multiplier": 2.0}
                },
                "highlights": ["Mall Road", "Patriata Chairlift"]
            },
            {
                "name": "Lahore",
                "region": "Punjab",
                "category": "Historical Places",
                "room_capacity": 2,
                "base_transport_cost_per_person": 2500,
                "base_accommodation_cost_per_room_night": 3500,
                "food_cost_per_person_day": 2000,
                "activities_misc_cost_per_person": 1500,
                "category_rates": {
                    "Budget": {"transport_multiplier": 1.0, "accommodation_per_room_night": 2500, "food_multiplier": 1.0, "activities_multiplier": 0.8},
                    "Standard": {"transport_multiplier": 1.3, "accommodation_per_room_night": 4500, "food_multiplier": 1.2, "activities_multiplier": 1.1},
                    "Premium": {"transport_multiplier": 2.0, "accommodation_per_room_night": 9000, "food_multiplier": 1.8, "activities_multiplier": 1.8}
                },
                "highlights": ["Lahore Fort", "Badshahi Mosque"]
            }
        ]
    }
    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(sample_data, f)

    p = TripPlanner(data_manager=dm)
    return p


class TestTripPlanner:
    def test_destination_filtering(self, planner):
        mountains = planner.filter_destinations_by_type("Mountains")
        assert len(mountains) == 1
        assert mountains[0].name == "Murree"

        all_dests = planner.filter_destinations_by_type("Any")
        assert len(all_dests) == 2

    def test_create_trip_plan(self, planner):
        plan = planner.create_trip_plan(
            destination_name="Murree",
            departure_city="Islamabad",
            travellers=2,
            days=3,
            nights=2,
            available_budget=60000.0,
            travel_category="Standard"
        )
        assert plan.destination_name == "Murree"
        assert plan.breakdown is not None
        assert plan.breakdown.feasibility_status == "Within Budget"
        assert len(plan.itinerary) == 3

    def test_itinerary_day_trip(self, planner):
        dest = planner.find_destination("Murree")
        itin = planner.generate_itinerary(dest, "Islamabad", days=1, nights=0)
        assert len(itin) == 1
        assert "Day Excursion" in itin[0]["title"]
        assert "None" in itin[0]["accommodation"]

    def test_dynamic_modification_cancellation(self, planner):
        plan = planner.create_trip_plan("Murree", "Islamabad", 2, 3, 2, available_budget=60000)
        original_budget = plan.available_budget
        original_travellers = plan.travellers

        # Modify travellers to 5
        planner.modify_current_plan(travellers=5, available_budget=30000)
        assert planner.current_plan.travellers == 5
        assert planner.current_plan.available_budget == 30000

        # Cancel modifications
        planner.cancel_modifications()
        assert planner.current_plan.travellers == original_travellers
        assert planner.current_plan.available_budget == original_budget

    def test_dynamic_modification_confirmation(self, planner):
        planner.create_trip_plan("Murree", "Islamabad", 2, 3, 2, available_budget=60000)
        planner.modify_current_plan(travel_category="Premium")
        planner.confirm_modifications()

        assert planner.current_plan.travel_category == "Premium"
        assert planner.current_plan._snapshot is None

    def test_confirm_and_save_plan(self, planner):
        planner.create_trip_plan("Murree", "Islamabad", 2, 3, 2, available_budget=60000)
        success = planner.confirm_and_save_current_plan()
        assert success is True
        assert planner.current_plan.is_confirmed is True

        saved_trips = planner.data_manager.load_trips()
        assert len(saved_trips) == 1
        assert saved_trips[0]["destination_name"] == "Murree"
