from collections import defaultdict, deque
from typing import List, Dict, Any, Optional
from models.destination import Destination
from models.trip import TripPlan, CostBreakdown
from services.trip_calculator import TripCostCalculator
from services.feasibility_checker import TripFeasibilityChecker
from services.trip_optimizer import TripOptimizer
from utils.data_manager import DataManager
from utils.validators import validate_trip_duration, validate_positive_number, validate_integer_range


class TripPlanner:
    """
    Main orchestrator for Module One: Pakistan Trip Planner.
    Manages destination catalogs, itinerary creation, dynamic parameter adjustments,
    snapshot rollback mechanisms, and plan confirmations.
    """

    def __init__(self, data_manager: Optional[DataManager] = None):
        self.data_manager = data_manager or DataManager()
        self.destinations: Dict[str, Destination] = {}
        self.destinations_by_type = defaultdict(list)
        self.history = deque(maxlen=50)

        # Active in-memory plan
        self.current_plan: Optional[TripPlan] = None
        self.optimizer: Optional[TripOptimizer] = None

        self.load_destinations()

    def load_destinations(self) -> None:
        """Load destinations from data storage and group by type."""
        raw_list = self.data_manager.load_destinations_raw()
        self.destinations.clear()
        self.destinations_by_type.clear()

        for d in raw_list:
            dest_obj = Destination.from_dict(d)
            self.destinations[dest_obj.name.lower()] = dest_obj
            self.destinations_by_type[dest_obj.category].append(dest_obj)

        self.optimizer = TripOptimizer(list(self.destinations.values()))
        self.history.append(f"Loaded {len(self.destinations)} destinations.")

    def get_all_destinations(self) -> List[Destination]:
        """Return list of all registered destinations."""
        return list(self.destinations.values())

    def find_destination(self, name: str) -> Optional[Destination]:
        """Find destination by case-insensitive name."""
        return self.destinations.get(str(name).strip().lower())

    def filter_destinations_by_type(self, dest_type: str) -> List[Destination]:
        """Filter destinations by type ('Mountains', 'Historical Places', 'Lakes & Nature', 'Any')."""
        if not dest_type or dest_type.lower() == "any":
            return self.get_all_destinations()
        matched = []
        for d in self.destinations.values():
            if d.category.lower() == dest_type.lower():
                matched.append(d)
        return matched

    def generate_itinerary(
        self,
        destination: Destination,
        departure_city: str,
        days: int,
        nights: int
    ) -> List[Dict[str, Any]]:
        """
        Generate day-wise itinerary according to duration, destination, days and nights.
        Adapts seamlessly to zero-night day trips as well as multi-day expeditions.
        """
        itinerary = []
        highlights = destination.highlights or [
            "Scenic photo stop & local sightseeing",
            "Cultural exploration & traditional bazaar tour",
            "Regional cuisine tasting & tea break"
        ]

        if days == 1 and nights == 0:
            # Single-day round excursion
            itinerary.append({
                "day": 1,
                "title": f"Day Excursion to {destination.name}",
                "description": (
                    f"Early morning departure from {departure_city}. Scenic drive to {destination.name}. "
                    f"Visit {highlights[0] if highlights else 'key attractions'}. "
                    f"Enjoy traditional lunch and afternoon activities. "
                    f"Evening return journey back to {departure_city}."
                ),
                "accommodation": "None (Same-day return journey)",
                "meals": "Lunch & Evening Tea included"
            })
            return itinerary

        # Multi-day trip
        for d in range(1, days + 1):
            if d == 1:
                # Arrival day
                title = f"Day 1: Journey from {departure_city} to {destination.name}"
                desc = (
                    f"Depart from {departure_city}. Enjoy panoramic drive and rest stops along the route. "
                    f"Arrival in {destination.name}. Check-in to accommodation. "
                    f"Evening orientation walk and visit: {highlights[0]}."
                )
                stay = f"Overnight stay at {destination.name}" if nights > 0 else "Evening rest"
                meals = "Lunch on transit, Welcome Dinner at destination"
            elif d == days:
                # Departure day
                title = f"Day {d}: Souvenirs & Return to {departure_city}"
                desc = (
                    f"Morning breakfast. Check-out and final photo stops or brief visit to local bazaar for souvenirs. "
                    f"Commence return journey back to {departure_city}. Arrival by evening."
                )
                stay = f"Arrive home at {departure_city}"
                meals = "Breakfast & Lunch on route"
            else:
                # Intermediate exploration days
                highlight_idx = (d - 2) % len(highlights)
                activity = highlights[highlight_idx]
                title = f"Day {d}: Exploring {destination.name} Highlights"
                desc = (
                    f"Full-day excursion exploring {activity}. "
                    f"Photography, cultural interactions, and authentic local cuisine. "
                    f"Leisurely evening stroll and mountain/city sunset."
                )
                stay = f"Overnight stay at {destination.name}" if d <= nights else f"Travel accommodation"
                meals = "Breakfast, Lunch, and Dinner"

            itinerary.append({
                "day": d,
                "title": title,
                "description": desc,
                "accommodation": stay,
                "meals": meals
            })

        return itinerary

    def create_trip_plan(
        self,
        destination_name: str,
        departure_city: str,
        travellers: int,
        days: int,
        nights: int,
        available_budget: float,
        travel_category: str = "Standard",
        transport_preference: str = "Standard AC Bus/Car",
        accommodation_preference: str = "Standard Hotel Room",
        destination_type: str = "Any",
        emergency_percentage: float = 10.0
    ) -> TripPlan:
        """
        Create, calculate, and register a new trip plan.
        """
        dest = self.find_destination(destination_name)
        if not dest:
            raise ValueError(f"Unknown destination: '{destination_name}'.")

        itinerary = self.generate_itinerary(dest, departure_city, days, nights)

        plan = TripPlan(
            destination_name=dest.name,
            departure_city=departure_city,
            travellers=travellers,
            days=days,
            nights=nights,
            available_budget=available_budget,
            travel_category=travel_category,
            transport_preference=transport_preference,
            accommodation_preference=accommodation_preference,
            destination_type=destination_type,
            emergency_percentage=emergency_percentage,
            itinerary=itinerary
        )

        # Compute cost breakdown
        plan.breakdown = TripCostCalculator.calculate_cost(
            destination=dest,
            travellers=travellers,
            days=days,
            nights=nights,
            available_budget=available_budget,
            travel_category=travel_category,
            emergency_percentage=emergency_percentage
        )

        self.current_plan = plan
        self.history.append(f"Created trip plan {plan.plan_id} for {dest.name}")
        return plan

    def modify_current_plan(
        self,
        destination_name: Optional[str] = None,
        departure_city: Optional[str] = None,
        travellers: Optional[int] = None,
        days: Optional[int] = None,
        nights: Optional[int] = None,
        available_budget: Optional[float] = None,
        travel_category: Optional[str] = None,
        transport_preference: Optional[str] = None,
        accommodation_preference: Optional[str] = None
    ) -> TripPlan:
        """
        Dynamically adjust trip parameters.
        Takes a snapshot beforehand so changes can be reverted if not confirmed.
        Recalculates all costs, breakdown, and itinerary.
        """
        if not self.current_plan:
            raise ValueError("No active trip plan to modify.")

        # Create rollback snapshot
        self.current_plan.create_snapshot()

        # Apply updates
        if destination_name:
            dest = self.find_destination(destination_name)
            if not dest:
                self.current_plan.restore_snapshot()
                raise ValueError(f"Unknown destination '{destination_name}'.")
            self.current_plan.destination_name = dest.name

        if departure_city:
            self.current_plan.departure_city = departure_city.strip()

        if travellers is not None:
            if travellers <= 0:
                self.current_plan.restore_snapshot()
                raise ValueError("Travellers count must be positive.")
            self.current_plan.travellers = travellers

        new_days = days if days is not None else self.current_plan.days
        new_nights = nights if nights is not None else self.current_plan.nights
        ok_dur, v_days, v_nights, err_dur = validate_trip_duration(new_days, new_nights)
        if not ok_dur:
            self.current_plan.restore_snapshot()
            raise ValueError(err_dur)

        self.current_plan.days = v_days
        self.current_plan.nights = v_nights

        if available_budget is not None:
            if available_budget < 0:
                self.current_plan.restore_snapshot()
                raise ValueError("Budget cannot be negative.")
            self.current_plan.available_budget = round(float(available_budget), 2)

        if travel_category:
            self.current_plan.travel_category = travel_category.strip().capitalize()

        if transport_preference:
            self.current_plan.transport_preference = transport_preference.strip()

        if accommodation_preference:
            self.current_plan.accommodation_preference = accommodation_preference.strip()

        # Regenerate itinerary and recalculate cost
        dest = self.find_destination(self.current_plan.destination_name)
        self.current_plan.itinerary = self.generate_itinerary(
            dest, self.current_plan.departure_city, self.current_plan.days, self.current_plan.nights
        )
        self.current_plan.breakdown = TripCostCalculator.calculate_cost(
            destination=dest,
            travellers=self.current_plan.travellers,
            days=self.current_plan.days,
            nights=self.current_plan.nights,
            available_budget=self.current_plan.available_budget,
            travel_category=self.current_plan.travel_category,
            emergency_percentage=self.current_plan.emergency_percentage
        )

        return self.current_plan

    def confirm_modifications(self) -> None:
        """Confirm modified parameters and clear snapshot."""
        if self.current_plan:
            self.current_plan.commit_changes()
            self.history.append(f"Confirmed modifications on plan {self.current_plan.plan_id}")

    def cancel_modifications(self) -> bool:
        """Cancel modifications and restore previous plan state."""
        if self.current_plan and self.current_plan.restore_snapshot():
            # Recompute breakdown for restored state
            dest = self.find_destination(self.current_plan.destination_name)
            self.current_plan.breakdown = TripCostCalculator.calculate_cost(
                destination=dest,
                travellers=self.current_plan.travellers,
                days=self.current_plan.days,
                nights=self.current_plan.nights,
                available_budget=self.current_plan.available_budget,
                travel_category=self.current_plan.travel_category,
                emergency_percentage=self.current_plan.emergency_percentage
            )
            self.history.append(f"Cancelled modifications. Rolled back plan {self.current_plan.plan_id}")
            return True
        return False

    def confirm_and_save_current_plan(self) -> bool:
        """Confirm final plan and persist to trips.json."""
        if not self.current_plan:
            return False
        self.current_plan.confirm_plan()
        success = self.data_manager.append_trip(self.current_plan.to_dict())
        if success:
            self.history.append(f"Saved confirmed trip {self.current_plan.plan_id}")
        return success

    def get_optimization_alternatives(self) -> Dict[str, Any]:
        """Get intelligent optimization recommendations if current plan is over-budget."""
        if not self.current_plan:
            return {"error": "No active plan."}
        if not self.optimizer:
            self.optimizer = TripOptimizer(self.get_all_destinations())
        return self.optimizer.generate_alternatives(self.current_plan, self.get_all_destinations())
